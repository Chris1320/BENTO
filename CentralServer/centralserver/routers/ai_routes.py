import datetime
from typing import Annotated, Any, Dict, Optional

import llm
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, desc, select

from centralserver.internals.auth_handler import (
    verify_access_token,
    verify_user_permission,
)
from centralserver.internals.config_handler import app_config
from centralserver.internals.db_handler import get_db_session
from centralserver.internals.logger import LoggerFactory
from centralserver.internals.models.ai import (
    AIInsightsRequest,
    AIInsightsResponse,
    ChatRequest,
    ChatResponse,
)
from centralserver.internals.models.reports.daily_financial_report import (
    DailyFinancialReport,
    DailyFinancialReportEntry,
)
from centralserver.internals.models.reports.monthly_report import MonthlyReport
from centralserver.internals.models.school import School
from centralserver.internals.models.token import DecodedJWTToken
from centralserver.internals.models.user import User

logger = LoggerFactory().get_logger(__name__)

router = APIRouter(
    prefix="/v1/ai",
    tags=["ai"],
)

logged_in_dep = Annotated[DecodedJWTToken, Depends(verify_access_token)]


async def get_llm_model():
    """Get the LLM model configured for the application."""

    try:
        gemini_api_key = app_config.ai.gemini_api_key
        if not gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API key is not configured",
            )

        # Get Gemini model
        try:
            model = llm.get_model(app_config.ai.gemini_model)
            model.key = gemini_api_key
            return model
        except Exception as e:
            logger.error("Failed to get Gemini model: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not available",
            ) from e

    except Exception as e:
        logger.error("AI service error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not available",
        ) from e


async def get_financial_data(
    session: Session, school_id: int, year: int, month: int
) -> Dict[str, Any]:
    """Get financial data for a specific school and time period."""

    try:
        # Create the monthly report ID (format: YYYY-MM-DD)
        monthly_report_id = f"{year}-{month:02d}-01"

        # Get monthly report for the school
        monthly_report = session.exec(
            select(MonthlyReport)
            .where(MonthlyReport.id == monthly_report_id)
            .where(MonthlyReport.submittedBySchool == school_id)
        ).first()

        # Get daily financial entries for this month
        daily_entries = session.exec(
            select(DailyFinancialReportEntry)
            .join(DailyFinancialReport)
            .where(DailyFinancialReport.parent == monthly_report_id)
            .join(MonthlyReport)
            .where(MonthlyReport.submittedBySchool == school_id)
        ).all()

        total_sales = sum(entry.sales for entry in daily_entries)
        total_purchases = sum(entry.purchases for entry in daily_entries)
        net_income = total_sales - total_purchases

        # Get previous month for comparison
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        prev_monthly_report_id = f"{prev_year}-{prev_month:02d}-01"

        prev_daily_entries = session.exec(
            select(DailyFinancialReportEntry)
            .join(DailyFinancialReport)
            .where(DailyFinancialReport.parent == prev_monthly_report_id)
            .join(MonthlyReport)
            .where(MonthlyReport.submittedBySchool == school_id)
        ).all()

        prev_total_sales = sum(entry.sales for entry in prev_daily_entries)
        prev_total_purchases = sum(entry.purchases for entry in prev_daily_entries)
        prev_net_income = prev_total_sales - prev_total_purchases

        return {
            "current_month": {
                "sales": total_sales,
                "purchases": total_purchases,
                "net_income": net_income,
                "entries_count": len(daily_entries),
                "report_status": (
                    monthly_report.reportStatus.value if monthly_report else "not_found"
                ),
            },
            "previous_month": {
                "sales": prev_total_sales,
                "purchases": prev_total_purchases,
                "net_income": prev_net_income,
                "entries_count": len(prev_daily_entries),
            },
            "trends": {
                "sales_change": total_sales - prev_total_sales,
                "purchases_change": total_purchases - prev_total_purchases,
                "net_income_change": net_income - prev_net_income,
            },
        }
    except Exception as e:
        logger.error("Error getting financial data: %s", e)

        return {
            "current_month": {
                "sales": 0,
                "purchases": 0,
                "net_income": 0,
                "entries_count": 0,
                "report_status": "error",
            },
            "previous_month": {
                "sales": 0,
                "purchases": 0,
                "net_income": 0,
                "entries_count": 0,
            },
            "trends": {
                "sales_change": 0,
                "purchases_change": 0,
                "net_income_change": 0,
            },
        }


async def get_user_school_context(
    session: Session, token: DecodedJWTToken, requested_school_id: Optional[int] = None
) -> tuple[School, bool]:
    """Get school context based on user permissions."""
    user = session.get(User, token.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user is admin (role ID 2 or 3)
    is_admin = user.roleId in [2, 3]

    if requested_school_id and is_admin:
        # Admin can access any school
        school = session.get(School, requested_school_id)
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
            )
        return school, is_admin
    elif user.schoolId:
        # Regular user can only access their own school
        school = session.get(School, user.schoolId)
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User's school not found"
            )
        return school, is_admin
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not assigned to a school",
        )


@router.post("/insights", response_model=AIInsightsResponse)
async def generate_financial_insights(
    request: AIInsightsRequest,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> AIInsightsResponse:
    """Generate AI insights for school financial data."""

    # Get user info to determine which school they belong to
    user = session.get(User, token.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Determine if user is requesting data for their own school or another school
    is_requesting_own_school = (
        request.school_id is None  # No school specified, defaults to user's school
        or request.school_id == user.schoolId  # Explicitly requesting their own school
    )

    # Check appropriate permission based on request
    if is_requesting_own_school:
        # User requesting their own school's data - check local permission
        has_permission = await verify_user_permission(
            "reports:local:read", session, token
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access your school's financial reports.",
            )
    else:
        # User requesting another school's data - check global permission
        has_permission = await verify_user_permission(
            "reports:global:read", session, token
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access other schools' financial reports.",
            )

    # Get school context
    school, _ = await get_user_school_context(session, token, request.school_id)

    # Ensure we have a school ID
    if not school.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Default to current month if not specified
    now = datetime.datetime.now()
    year = request.year or now.year
    month = request.month or now.month

    # Get financial data
    financial_data = await get_financial_data(session, school.id, year, month)

    # Get LLM model
    model = await get_llm_model()

    # Create prompt for insights
    month_name = datetime.date(year, month, 1).strftime("%B")
    period = f"{month_name} {year}"

    prompt = f"""
    Generate financial insights for {school.name} for {period}.
    
    Current month financial data:
    - Sales: ₱{financial_data['current_month']['sales']:,.2f}
    - Purchases: ₱{financial_data['current_month']['purchases']:,.2f}
    - Net Income: ₱{financial_data['current_month']['net_income']:,.2f}
    - Number of entries: {financial_data['current_month']['entries_count']}
    - Report Status: {financial_data['current_month']['report_status']}
    
    Previous month comparison:
    - Sales Change: ₱{financial_data['trends']['sales_change']:,.2f}
    - Purchases Change: ₱{financial_data['trends']['purchases_change']:,.2f}
    - Net Income Change: ₱{financial_data['trends']['net_income_change']:,.2f}
    
    Provide a concise financial insight in exactly 50 words or less. Focus on:
    1. Performance trends
    2. Key financial metrics
    3. Brief recommendations
    
    Be specific about the school's financial performance and actionable insights.
    """

    try:
        response = model.prompt(prompt)  # type: ignore
        insights_text = response.text().strip()

        # Ensure it's within 50 words
        # words = insights_text.split()
        # if len(words) > 50:
        #     insights_text = " ".join(words[:50]) + "..."

        return AIInsightsResponse(
            insights=insights_text, school_name=school.name, period=period
        )

    except Exception as e:
        logger.error("Error generating insights: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights",
        ) from e


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> ChatResponse:
    """Chat with AI about school financial data."""

    # Get user info to determine which school they belong to
    user = session.get(User, token.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Determine if user is requesting data for their own school or another school
    is_requesting_own_school = (
        request.school_id is None  # No school specified, defaults to user's school
        or request.school_id == user.schoolId  # Explicitly requesting their own school
    )

    # Check appropriate permission based on request
    if is_requesting_own_school:
        # User requesting their own school's data - check local permission
        has_permission = await verify_user_permission(
            "reports:local:read", session, token
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access your school's financial reports.",
            )
    else:
        # User requesting another school's data - check global permission
        has_permission = await verify_user_permission(
            "reports:global:read", session, token
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access other schools' financial reports.",
            )

    # Get school context
    school, _ = await get_user_school_context(session, token, request.school_id)

    # Ensure we have a school ID
    if not school.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Get current financial data
    now = datetime.datetime.now()
    financial_data = await get_financial_data(session, school.id, now.year, now.month)

    # Get recent monthly reports
    recent_reports = session.exec(
        select(MonthlyReport)
        .where(MonthlyReport.submittedBySchool == school.id)
        .order_by(desc(MonthlyReport.dateCreated))
        .limit(6)
    ).all()

    # Get LLM model
    model = await get_llm_model()

    # Create system prompt with school context
    system_prompt = f"""
    You are a financial assistant for {school.name}. You can only provide information about this school's financial data.
    
    Current financial summary:
    - Current Month Sales: ₱{financial_data['current_month']['sales']:,.2f}
    - Current Month Purchases: ₱{financial_data['current_month']['purchases']:,.2f}
    - Current Month Net Income: ₱{financial_data['current_month']['net_income']:,.2f}
    - Active Entries: {financial_data['current_month']['entries_count']}
    
    Recent trends:
    - Sales Change: ₱{financial_data['trends']['sales_change']:,.2f}
    - Purchases Change: ₱{financial_data['trends']['purchases_change']:,.2f}
    - Net Income Change: ₱{financial_data['trends']['net_income_change']:,.2f}
    
    Recent reports count: {len(recent_reports)}
    
    Rules:
    1. Only discuss {school.name}'s financial data
    2. Be helpful and provide actionable insights
    3. If asked about other schools, politely decline
    4. Use Philippine peso (₱) for currency
    5. Keep responses concise and professional
    """

    # Build conversation history
    conversation_messages: list[str] = []
    for msg in request.conversation_history:
        conversation_messages.append(f"{msg.role}: {msg.content}")

    conversation_context = "\n".join(conversation_messages[-10:])  # Last 10 messages

    # Create the full prompt
    full_prompt = f"""
    {system_prompt}
    
    Previous conversation:
    {conversation_context}
    
    User: {request.message}
    
    Assistant:"""

    try:
        response = model.prompt(full_prompt)  # type: ignore
        response_text = response.text().strip()

        return ChatResponse(response=response_text, school_name=school.name)

    except Exception as e:
        logger.error("Error in chat: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request",
        ) from e


@router.get("/status")
async def get_ai_status(
    token: logged_in_dep,
    session: Annotated[Session, Depends(get_db_session)],
) -> Dict[str, Any]:
    """Get AI service status."""

    try:
        # Check if Gemini API key is configured
        gemini_api_key = app_config.ai.gemini_api_key
        if not gemini_api_key:
            return {
                "status": "unavailable",
                "message": "Gemini API key is not configured",
                "features": {"insights": False, "chat": False},
            }

        # Try to get model
        model = await get_llm_model()

        # Test with a simple prompt
        _ = model.prompt("Test")  # type: ignore

        return {
            "status": "available",
            "message": "AI service is operational",
            "model": "gemini-1.5-flash-latest",
            "features": {"insights": True, "chat": True},
        }

    except Exception as e:
        logger.error("AI status check failed: %s", e)
        return {
            "status": "error",
            "message": f"AI service error: {str(e)}",
            "features": {"insights": False, "chat": False},
        }

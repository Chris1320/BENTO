import { defineConfig } from "@hey-api/openapi-ts";

import "dotenv/config";

export default defineConfig({
    input: {
        path: `${process.env.NEXT_PUBLIC_CENTRAL_SERVER_ENDPOINT}/openapi.json`,
        // watch: true,
    },
    output: {
        path: "src/lib/api/csclient",
        format: "prettier",
        lint: "eslint",
    },
    parser: {
        pagination: { keywords: ["limit", "offset"] },
    },
    plugins: [
        {
            name: "@hey-api/client-fetch",
            runtimeConfigPath: "./src/lib/api/customClient.ts",
        },
    ],
});

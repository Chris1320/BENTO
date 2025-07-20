import type { NextConfig } from "next";
import { codecovNextJSWebpackPlugin } from "@codecov/nextjs-webpack-plugin";

// eslint-disable-next-line @typescript-eslint/no-require-imports
const withPWA = require("next-pwa")({
    dest: "public",
    disable: process.env.NODE_ENV === "development",
    register: true,
    skipWaiting: true,
    fallbacks: {
        document: "/_offline",
        image: "/icon-512x512.png",
    },
    runtimeCaching: [
        {
            urlPattern: /^https?.*\/api\/.*$/,
            handler: "NetworkFirst",
            options: {
                cacheName: "api-cache",
                networkTimeoutSeconds: 10,
                expiration: {
                    maxEntries: 100,
                    maxAgeSeconds: 24 * 60 * 60, // 24 hours
                },
                cacheableResponse: {
                    statuses: [0, 200],
                },
            },
        },
        {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
            handler: "CacheFirst",
            options: {
                cacheName: "images-cache",
                expiration: {
                    maxEntries: 100,
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
                },
            },
        },
        {
            urlPattern: /\.(?:js|css|woff|woff2|ttf|eot)$/,
            handler: "CacheFirst",
            options: {
                cacheName: "static-resources",
                expiration: {
                    maxEntries: 100,
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
                },
            },
        },
        {
            urlPattern: /^https?.*$/,
            handler: "NetworkFirst",
            options: {
                cacheName: "offlineCache",
                networkTimeoutSeconds: 15,
                expiration: {
                    maxEntries: 200,
                    maxAgeSeconds: 24 * 60 * 60, // 24 hours
                },
                cacheableResponse: {
                    statuses: [0, 200],
                },
            },
        },
    ],
});

const nextConfig: NextConfig = {
    devIndicators: process.env.NODE_ENV !== "production" ? {} : false,
    experimental: {
        optimizePackageImports: ["@mantine/core", "@mantine/hooks"],
    },
    async headers() {
        return [
            {
                source: "/(.*)",
                headers: [
                    {
                        key: "X-Content-Type-Options",
                        value: "nosniff",
                    },
                    {
                        key: "X-Frame-Options",
                        value: "DENY",
                    },
                    {
                        key: "Referrer-Policy",
                        value: "strict-origin-when-cross-origin",
                    },
                ],
            },
            {
                source: "/sw.js",
                headers: [
                    {
                        key: "Content-Type",
                        value: "application/javascript; charset=utf-8",
                    },
                    {
                        key: "Cache-Control",
                        value: "no-cache, no-store, must-revalidate",
                    },
                    {
                        key: "Content-Security-Policy",
                        value: "default-src 'self'; script-src 'self'",
                    },
                ],
            },
        ];
    },
    webpack: (config, options) => {
        config.plugins.push(
            codecovNextJSWebpackPlugin({
                enableBundleAnalysis: process.env.CODECOV_TOKEN !== undefined,
                bundleName: "webclient-bundle",
                uploadToken: process.env.CODECOV_TOKEN,
                webpack: options.webpack,
            })
        );

        return config;
    },
};

export default withPWA(nextConfig);

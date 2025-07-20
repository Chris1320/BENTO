// Type declarations for missing modules used by next-pwa
declare module 'minimatch'

// Additional PWA-related type declarations
declare module 'workbox-*' {
  const content: unknown
  export = content
}

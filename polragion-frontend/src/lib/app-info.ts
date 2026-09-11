/**
 * Single source of truth for the metadata shown in the About section and the sidebar footer.
 */
export const APP_INFO = {
    name: "Polragion",
    tagline: "Ask your work items",
    /** Injected by Vite from the version field in package.json. */
    version: __APP_VERSION__,
    author: "Michael Froschauer",
    copyrightSince: 2026,
    license: "GNU GPL v3.0",
    licenseUrl: "https://www.gnu.org/licenses/gpl-3.0.html",
    repositoryUrl: "https://github.com/MichaelFroschauer/polragion",
    /** Context of the project, shown below the copyright details. */
    attribution: "A personal hobby project, built in my spare time.",
} as const

/** e.g. "© 2026 Michael Froschauer" */
export function copyrightNotice(year: number = new Date().getFullYear()): string {
    const range =
        year > APP_INFO.copyrightSince ? `${APP_INFO.copyrightSince}-${year}` : `${APP_INFO.copyrightSince}`

    return `© ${range} ${APP_INFO.author}`
}

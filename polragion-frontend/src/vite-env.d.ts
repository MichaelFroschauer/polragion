/// <reference types="vite/client" />

/** App version, injected by Vite from package.json. */
declare const __APP_VERSION__: string;

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_POLARION_WEB_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

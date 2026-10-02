# Arquivos locais de estimativa de pose

- `pose_landmarker_lite.task`: modelo oficial Pose Landmarker Lite, obtido em 2026-10-01 de `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`.
- SHA-256 do modelo: `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`.
- `vision_wasm_internal.*` e `vision_wasm_nosimd_internal.*`: cópias dos arquivos distribuídos com `@mediapipe/tasks-vision` versão 1.0.1, instalado pelo npm.

Esses arquivos são servidos pela própria aplicação. A página carrega o modelo somente após a ativação explícita da câmera. Consulte a [documentação oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/web_js) e o [aviso de privacidade do MediaPipe](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/web/vision/README.md#privacy-notice).

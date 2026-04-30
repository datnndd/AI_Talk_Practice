import { useEffect, useRef, useState } from "react";
import { CircleNotch, Robot, WarningCircle } from "@phosphor-icons/react";
import * as PIXI from "pixi.js";

const FALLBACK_MODEL_URL = import.meta.env.VITE_LIVE2D_MODEL_URL || "";
const FALLBACK_CORE_URL = import.meta.env.VITE_LIVE2D_CORE_URL || "";

const STATUS_COPY = {
  idle: "Ready",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
  connecting: "Connecting",
  reconnecting: "Reconnecting",
  error: "Needs attention",
  ended: "Completed",
};

const STATUS_STYLE = {
  idle: "border-zinc-200 bg-zinc-50 text-zinc-600",
  listening: "border-primary/20 bg-primary/10 text-primary",
  thinking: "border-amber-200 bg-amber-50 text-amber-700",
  speaking: "border-emerald-200 bg-emerald-50 text-emerald-700",
  connecting: "border-sky-200 bg-sky-50 text-sky-700",
  reconnecting: "border-sky-200 bg-sky-50 text-sky-700",
  error: "border-rose-200 bg-rose-50 text-rose-700",
  ended: "border-emerald-200 bg-emerald-50 text-emerald-700",
};

const MOTION_GROUP_BY_STATUS = {
  idle: "Idle",
  listening: "Listen",
  thinking: "Think",
  speaking: "Talk",
  ended: "Success",
};

const EXPRESSION_BY_STATUS = {
  idle: "neutral",
  listening: "focused",
  thinking: "focused",
  speaking: "talk",
  connecting: "focused",
  reconnecting: "focused",
  error: "focused",
  ended: "happy",
};

const LIP_SYNC_PARAMETER_ID = "ParamMouthOpenY";
const LIP_SYNC_SMOOTHING = 0.35;

const scriptLoaders = new Map();

const loadScriptOnce = (src) => {
  if (window.Live2DCubismCore) {
    return Promise.resolve();
  }

  if (scriptLoaders.has(src)) {
    return scriptLoaders.get(src);
  }

  const promise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[data-live2d-core="${src}"]`);
    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(), { once: true });
      existingScript.addEventListener("error", () => reject(new Error("Live2D Cubism core failed to load.")), { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.dataset.live2dCore = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Live2D Cubism core failed to load."));
    document.head.appendChild(script);
  });

  scriptLoaders.set(src, promise);
  return promise;
};

const hasMotionGroup = (model, group) => {
  const motions = model?.internalModel?.settings?.motions;
  return Boolean(group && Array.isArray(motions?.[group]) && motions[group].length > 0);
};

const hasExpression = (model, expressionName) => {
  if (!expressionName) {
    return false;
  }

  const manager = model?.internalModel?.motionManager?.expressionManager;
  if (!manager) {
    return false;
  }

  if (typeof manager.getExpressionIndex === "function") {
    return manager.getExpressionIndex(expressionName) >= 0;
  }

  return Boolean(manager.definitions?.some((item) => item?.Name === expressionName || item?.name === expressionName));
};

const fitModelToContainer = (app, model, container) => {
  if (!app || !model || !container) {
    return;
  }

  const width = Math.max(container.clientWidth, 1);
  const height = Math.max(container.clientHeight, 1);
  app.renderer.resize(width, height);

  const modelWidth = model.internalModel?.width || model.width || 1;
  const modelHeight = model.internalModel?.height || model.height || 1;
  const scale = Math.min(width / (modelWidth * 1.02), height / (modelHeight * 0.88));

  model.anchor?.set(0.5, 1);
  model.scale.set(Math.max(scale, 0.01));
  model.x = width / 2;
  model.y = height * 0.92;
};

const patchCubismCoreCompatibility = (model) => {
  const coreModel = model?.internalModel?.coreModel?._model;
  const drawables = coreModel?.drawables;

  if (!drawables || drawables.renderOrders) {
    return;
  }

  if (coreModel.renderOrders) {
    drawables.renderOrders = typeof coreModel.renderOrders.subarray === "function"
      ? coreModel.renderOrders.subarray(0, drawables.count)
      : coreModel.renderOrders;
    return;
  }

  if (drawables.drawOrders) {
    drawables.renderOrders = drawables.drawOrders;
  }
};

const setMouthOpen = (model, value) => {
  const coreModel = model?.internalModel?.coreModel;
  if (!coreModel || typeof coreModel.setParameterValueById !== "function") {
    return;
  }

  try {
    coreModel.setParameterValueById(LIP_SYNC_PARAMETER_ID, Math.max(0, Math.min(1, value)));
  } catch {
    // Some supplied models may not expose a mouth-open parameter.
  }
};

const applyAvatarState = async (model, status, runtime) => {
  if (!model || !runtime) {
    return;
  }

  const expressionName = EXPRESSION_BY_STATUS[status];
  if (hasExpression(model, expressionName)) {
    try {
      await model.expression(expressionName);
    } catch {
      // Optional expressions vary per model; missing or failed expressions should not break practice.
    }
  }

  const motionGroup = MOTION_GROUP_BY_STATUS[status];
  if (!hasMotionGroup(model, motionGroup)) {
    return;
  }

  try {
    const priority = status === "idle" ? runtime.MotionPriority.IDLE : runtime.MotionPriority.NORMAL;
    await model.motion(motionGroup, undefined, priority);
  } catch {
    // Motion availability depends on the supplied model contract.
  }
};

const Live2DFallback = ({ status, scenarioTitle, errorMessage }) => {
  const statusText = STATUS_COPY[status] || STATUS_COPY.idle;

  return (
    <div className="flex h-full min-h-[180px] flex-col justify-between bg-[linear-gradient(180deg,_#ffffff_0%,_#f8fafc_100%)] p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">AI Partner</p>
          <p className="mt-1 truncate text-sm font-black text-zinc-950">{scenarioTitle || "Speaking partner"}</p>
        </div>
        <span className={`shrink-0 rounded-lg border px-2.5 py-1 text-xs font-bold ${STATUS_STYLE[status] || STATUS_STYLE.idle}`}>
          {statusText}
        </span>
      </div>

      <div className="flex flex-1 items-center justify-center py-6">
        <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-zinc-200 bg-white text-zinc-400 shadow-sm">
          <Robot size={48} weight="duotone" />
          {status === "listening" || status === "speaking" ? (
            <span className="absolute -right-1 top-4 h-4 w-4 rounded-full bg-emerald-400 ring-4 ring-emerald-100" />
          ) : null}
        </div>
      </div>

      {errorMessage ? (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold leading-relaxed text-amber-800">
          <WarningCircle size={16} weight="fill" className="mt-0.5 shrink-0" />
          <span>Live2D chưa sẵn sàng. Kiểm tra model và Cubism core asset.</span>
        </div>
      ) : null}
    </div>
  );
};

const Live2DAvatarPanel = ({
  status = "idle",
  scenarioTitle = "",
  lipSyncLevel = 0,
  modelUrl = "",
  coreUrl = "",
}) => {
  const containerRef = useRef(null);
  const modelRef = useRef(null);
  const runtimeRef = useRef(null);
  const lipSyncTargetRef = useRef(0);
  const lipSyncCurrentRef = useRef(0);
  const lastMotionStatusRef = useRef("");
  const [loadState, setLoadState] = useState("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const effectiveModelUrl = modelUrl || FALLBACK_MODEL_URL;
  const effectiveCoreUrl = coreUrl || FALLBACK_CORE_URL;

  useEffect(() => {
    lipSyncTargetRef.current = Math.max(0, Math.min(1, lipSyncLevel));
  }, [lipSyncLevel]);

  useEffect(() => {
    let isDisposed = false;
    let app = null;
    let resizeObserver = null;
    let lipSyncTicker = null;

    const setup = async () => {
      try {
        setLoadState("loading");
        setErrorMessage("");
        if (!containerRef.current) {
          return;
        }
        if (!effectiveModelUrl || !effectiveCoreUrl) {
          throw new Error("Live2D model or Cubism core URL is missing.");
        }

        window.PIXI = PIXI;
        await loadScriptOnce(effectiveCoreUrl);
        const runtime = await import("pixi-live2d-display/cubism4");

        if (isDisposed || !containerRef.current) {
          return;
        }

        runtimeRef.current = runtime;

        app = new PIXI.Application({
          antialias: true,
          autoDensity: true,
          backgroundAlpha: 0,
          height: Math.max(containerRef.current.clientHeight, 1),
          resolution: window.devicePixelRatio || 1,
          width: Math.max(containerRef.current.clientWidth, 1),
        });

        app.view.className = "h-full w-full";
        containerRef.current.textContent = "";
        containerRef.current.appendChild(app.view);

        const model = await runtime.Live2DModel.from(effectiveModelUrl, {
          autoInteract: false,
          motionPreload: runtime.MotionPreloadStrategy.IDLE,
        });

        if (isDisposed || !containerRef.current) {
          model.destroy();
          return;
        }

        patchCubismCoreCompatibility(model);
        modelRef.current = model;
        app.stage.addChild(model);
        fitModelToContainer(app, model, containerRef.current);

        lipSyncTicker = () => {
          const target = lipSyncTargetRef.current;
          const current = lipSyncCurrentRef.current;
          const next = Math.abs(target - current) < 0.01
            ? target
            : current + (target - current) * LIP_SYNC_SMOOTHING;
          lipSyncCurrentRef.current = next;
          setMouthOpen(model, next);
        };
        app.ticker.add(lipSyncTicker);

        resizeObserver = new ResizeObserver(() => {
          fitModelToContainer(app, model, containerRef.current);
        });
        resizeObserver.observe(containerRef.current);

        setLoadState("ready");
      } catch (error) {
        if (!isDisposed) {
          setErrorMessage(error?.message || "Live2D failed to load.");
          setLoadState("error");
        }
      }
    };

    void setup();

    return () => {
      isDisposed = true;
      resizeObserver?.disconnect();
      modelRef.current = null;
      runtimeRef.current = null;
      lastMotionStatusRef.current = "";
      if (app) {
        if (lipSyncTicker) {
          app.ticker.remove(lipSyncTicker);
        }
        app.destroy(true, {
          baseTexture: true,
          children: true,
          texture: true,
        });
      }
    };
  }, [effectiveCoreUrl, effectiveModelUrl]);

  useEffect(() => {
    if (loadState !== "ready" || !modelRef.current || !runtimeRef.current || lastMotionStatusRef.current === status) {
      return;
    }

    lastMotionStatusRef.current = status;
    void applyAvatarState(modelRef.current, status, runtimeRef.current);
  }, [loadState, status]);

  const statusText = STATUS_COPY[status] || STATUS_COPY.idle;

  return (
    <section className="relative flex min-h-[190px] w-full flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white shadow-[0_20px_54px_-42px_rgba(15,23,42,0.55)] lg:min-h-0">
      {loadState === "error" ? (
        <Live2DFallback status={status} scenarioTitle={scenarioTitle} errorMessage={errorMessage} />
      ) : (
        <>
          <div className="pointer-events-none absolute left-4 right-4 top-4 z-10 flex items-center justify-between gap-3">
            <div className="min-w-0 rounded-lg border border-white/70 bg-white/80 px-3 py-2 shadow-sm backdrop-blur-md">
              <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-zinc-400">AI Partner</p>
              <p className="mt-0.5 truncate text-sm font-black text-zinc-950">{scenarioTitle || "Speaking partner"}</p>
            </div>
            <span className={`shrink-0 rounded-lg border px-2.5 py-1 text-xs font-bold shadow-sm backdrop-blur-md ${STATUS_STYLE[status] || STATUS_STYLE.idle}`}>
              {statusText}
            </span>
          </div>

          <div
            ref={containerRef}
            className="min-h-[190px] flex-1 bg-[radial-gradient(circle_at_50%_35%,_rgba(229,245,255,0.95),_rgba(255,255,255,0)_54%),linear-gradient(180deg,_#ffffff_0%,_#f8fafc_100%)] lg:min-h-0"
            data-testid="live2d-canvas-host"
          />
          {loadState === "loading" ? (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-zinc-400">
              <CircleNotch size={28} className="animate-spin" />
            </div>
          ) : null}
        </>
      )}
    </section>
  );
};

export default Live2DAvatarPanel;

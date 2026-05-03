import { useEffect, useRef, useState } from "react";
import { CircleNotch, Robot, WarningCircle } from "@phosphor-icons/react";
import * as PIXI from "pixi.js";

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

  const rect = container.getBoundingClientRect();
  const width = Math.max(container.clientWidth, Math.round(rect.width), 1);
  const height = Math.max(container.clientHeight, Math.round(rect.height), 1);
  app.renderer.resize(width, height);

  const modelWidth = model.internalModel?.width || model.width || 1;
  const modelHeight = model.internalModel?.height || model.height || 1;
  const scale = Math.min(width / (modelWidth * 1.02), height / (modelHeight * 0.88));

  model.anchor?.set(0.5, 1);
  model.scale.set(Math.max(scale, 0.01));
  model.x = width / 2;
  model.y = height * 1.04;
};

const isRenderableContainer = (container) => {
  if (!container) {
    return false;
  }

  const rect = container.getBoundingClientRect();
  return container.getClientRects().length > 0 && rect.width > 2 && rect.height > 2;
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

const destroyPixiAppSafely = (app, container, model, lipSyncTicker) => {
  if (!app) {
    return;
  }

  if (lipSyncTicker) {
    app.ticker.remove(lipSyncTicker);
  }

  if (model && app.stage?.children?.includes(model)) {
    app.stage.removeChild(model);
  }

  if (container && app.view?.parentNode === container) {
    container.removeChild(app.view);
  }

  app.destroy(false, {
    children: false,
    texture: false,
    baseTexture: false,
  });
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
    <div className="flex h-full min-h-[180px] flex-col justify-between bg-card p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--page-subtle)]">AI Partner</p>
          <p className="mt-1 truncate text-sm font-black text-[var(--page-fg)]">{scenarioTitle || "Speaking partner"}</p>
        </div>
        <span className={`shrink-0 rounded-lg border px-2.5 py-1 text-xs font-bold ${STATUS_STYLE[status] || STATUS_STYLE.idle}`}>
          {statusText}
        </span>
      </div>

      <div className="flex flex-1 items-center justify-center py-6">
        <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-border bg-card text-[var(--page-subtle)] shadow-sm">
          <Robot size={48} weight="duotone" />
          {status === "listening" || status === "speaking" ? (
            <span className="absolute -right-1 top-4 h-4 w-4 rounded-full bg-emerald-400 ring-4 ring-emerald-100" />
          ) : null}
        </div>
      </div>

      {errorMessage ? (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold leading-relaxed text-amber-800">
          <WarningCircle size={16} weight="fill" className="mt-0.5 shrink-0" />
          <span>Live2D chưa sẵn sàng: {errorMessage}</span>
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
  className = "",
  canvasClassName = "",
}) => {
  const containerRef = useRef(null);
  const appRef = useRef(null);
  const setupIdRef = useRef(0);
  const modelRef = useRef(null);
  const runtimeRef = useRef(null);
  const lipSyncTargetRef = useRef(0);
  const lipSyncCurrentRef = useRef(0);
  const lastMotionStatusRef = useRef("");
  const [isRenderable, setIsRenderable] = useState(false);
  const [loadState, setLoadState] = useState("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const effectiveModelUrl = modelUrl || "";
  const effectiveCoreUrl = coreUrl || "";

  useEffect(() => {
    let frame = 0;
    const updateRenderable = () => {
      if (frame) {
        cancelAnimationFrame(frame);
      }

      frame = requestAnimationFrame(() => {
        frame = 0;
        setIsRenderable(isRenderableContainer(containerRef.current));
      });
    };

    const resizeObserver = new ResizeObserver(updateRenderable);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    window.addEventListener("resize", updateRenderable);
    updateRenderable();

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateRenderable);
      if (frame) {
        cancelAnimationFrame(frame);
      }
    };
  }, []);

  useEffect(() => {
    lipSyncTargetRef.current = Math.max(0, Math.min(1, lipSyncLevel));
  }, [lipSyncLevel]);

  useEffect(() => {
    if (!isRenderable) {
      return undefined;
    }

    const setupId = setupIdRef.current + 1;
    setupIdRef.current = setupId;
    let isDisposed = false;
    let app = null;
    let model = null;
    let hostContainer = null;
    let resizeObserver = null;
    let resizeFrame = 0;
    let lipSyncTicker = null;

    const isCurrentSetup = () => !isDisposed && setupIdRef.current === setupId && isRenderableContainer(containerRef.current);
    const requestFit = () => {
      if (!app || !model || !hostContainer) {
        return;
      }

      if (resizeFrame) {
        cancelAnimationFrame(resizeFrame);
      }
      resizeFrame = requestAnimationFrame(() => {
        resizeFrame = 0;
        if (isCurrentSetup()) {
          fitModelToContainer(app, model, hostContainer);
        }
      });
    };

    const setup = async () => {
      try {
        setLoadState("loading");
        setErrorMessage("");
        const container = containerRef.current;
        if (!container) {
          return;
        }
        hostContainer = container;

        container.textContent = "";
        modelRef.current = null;
        runtimeRef.current = null;
        lastMotionStatusRef.current = "";

        if (!effectiveModelUrl || !effectiveCoreUrl) {
          throw new Error("Live2D model or Cubism core URL is missing.");
        }

        window.PIXI = PIXI;
        await loadScriptOnce(effectiveCoreUrl);
        if (!isCurrentSetup()) {
          return;
        }

        const runtime = await import("pixi-live2d-display/cubism4");

        if (!isCurrentSetup()) {
          return;
        }

        runtimeRef.current = runtime;

        app = new PIXI.Application({
          antialias: true,
          autoDensity: true,
          backgroundAlpha: 0,
          height: Math.max(container.clientHeight, 1),
          resolution: window.devicePixelRatio || 1,
          width: Math.max(container.clientWidth, 1),
        });
        appRef.current = app;

        app.view.className = "h-full w-full";
        container.textContent = "";
        container.appendChild(app.view);

        model = await runtime.Live2DModel.from(effectiveModelUrl, {
          autoInteract: false,
          motionPreload: runtime.MotionPreloadStrategy.IDLE,
        });

        if (!isCurrentSetup()) {
          destroyPixiAppSafely(app, container, model, lipSyncTicker);
          return;
        }

        patchCubismCoreCompatibility(model);
        modelRef.current = model;
        app.stage.addChild(model);
        fitModelToContainer(app, model, container);

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

        resizeObserver = new ResizeObserver(requestFit);
        resizeObserver.observe(container);
        window.addEventListener("resize", requestFit);
        requestFit();

        if (isCurrentSetup()) {
          setLoadState("ready");
        }
      } catch (error) {
        if (!isDisposed && setupIdRef.current === setupId) {
          setErrorMessage(error?.message || "Live2D failed to load.");
          setLoadState("error");
        }
      }
    };

    void setup();

    return () => {
      isDisposed = true;
      resizeObserver?.disconnect();
      if (resizeFrame) {
        cancelAnimationFrame(resizeFrame);
      }
      window.removeEventListener("resize", requestFit);
      lipSyncTargetRef.current = 0;
      lipSyncCurrentRef.current = 0;
      if (setupIdRef.current === setupId) {
        modelRef.current = null;
        runtimeRef.current = null;
        appRef.current = null;
        lastMotionStatusRef.current = "";
      }
      destroyPixiAppSafely(app, hostContainer, model, lipSyncTicker);
    };
  }, [effectiveCoreUrl, effectiveModelUrl, isRenderable]);

  useEffect(() => {
    if (loadState !== "ready" || !modelRef.current || !runtimeRef.current || lastMotionStatusRef.current === status) {
      return;
    }

    lastMotionStatusRef.current = status;
    void applyAvatarState(modelRef.current, status, runtimeRef.current);
  }, [loadState, status]);

  return (
    <section className={`relative flex min-h-[190px] w-full flex-col overflow-hidden rounded-lg border border-border bg-card shadow-[0_20px_54px_-42px_rgba(15,23,42,0.55)] ${className}`}>
      {loadState === "error" ? (
        <Live2DFallback status={status} scenarioTitle={scenarioTitle} errorMessage={errorMessage} />
      ) : (
        <>
          <div
            ref={containerRef}
            className={`min-h-[190px] flex-1 bg-transparent ${canvasClassName}`}
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

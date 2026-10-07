'use client';

// Mesh-drift WebGL background, adapted from the 21st.dev Shader Builder
// "Hero background" (athenasolutionscompany). Zero dependencies: one canvas
// that fills its parent. Retinted to the app's ink / louage red / amber, and
// it renders a single still frame for reduced-motion users, when the canvas
// is off-screen, or when the tab is hidden.

import { useEffect, useRef } from 'react';

const VERT = `attribute vec2 a_position;
void main() { gl_Position = vec4(a_position, 0.0, 1.0); }`;

const FRAG = `precision mediump float;
uniform vec3 u_colors[4];
uniform vec3 u_scene;   // resolution.xy, time
uniform vec4 u_cursor;  // pointer.xy, presence, strength

float hash21(vec2 p) {
  p = mod(p, 31.0);
  p = fract(p * vec2(234.34, 435.345));
  p += dot(p, p + 34.23);
  return fract(p.x * p.y);
}
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash21(i), hash21(i + vec2(1.0, 0.0)), u.x),
             mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
  float v = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { v += a * noise(p); p = p * 2.03 + vec2(17.0, 9.2); a *= 0.5; }
  return v;
}
float grain(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
vec3 shade(vec2 p, float t) {
  vec3 acc = u_colors[0] * 0.15;
  float total = 0.15;
  for (int i = 0; i < 4; i++) {
    float fi = float(i);
    vec2 c = vec2(sin(t * (0.21 + fi * 0.071) + fi * 2.4 + 9.0),
                  cos(t * (0.17 + fi * 0.093) + fi * 1.7)) * 0.65;
    float w = exp(-dot(p - c, p - c) * 6.0);
    acc += u_colors[i] * w;
    total += w;
  }
  return acc / total;
}
void main() {
  vec2 res = u_scene.xy;
  vec2 uv = gl_FragCoord.xy / res;
  vec2 p = (gl_FragCoord.xy - 0.5 * res) / min(res.x, res.y);
  // Cursor swirl: the field twists gently around the pointer.
  vec2 cursor = (0.5 * u_cursor.xy * res) / min(res.x, res.y);
  vec2 d = p - cursor;
  float mask = u_cursor.z * (1.0 - smoothstep(0.0, 0.4, length(d)));
  float ang = mask * u_cursor.w * 2.2;
  p = cursor + mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * d;
  p *= 1.3;
  float t = u_scene.z;
  p += 0.15 * vec2(sin(t * 0.31), cos(t * 0.23));
  p += 0.2 * (vec2(fbm(p * 2.0 + 3.0), fbm(p * 2.0 + vec2(5.2, 1.3))) - 0.5);
  vec3 col = shade(p, t);
  col = (col - 0.5) * 1.15 + 0.5;
  col *= 1.0 - 0.25 * smoothstep(0.35, 1.0, length(uv - 0.5) * 1.414);
  col += (grain(gl_FragCoord.xy) - 0.5) * 0.08;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

// Mostly ink, with a red current and a faint sodium-amber glow.
const COLORS = [
  [0.055, 0.059, 0.071],
  [0.62, 0.11, 0.13],
  [0.07, 0.075, 0.09],
  [0.55, 0.33, 0.04],
];
const TIME_SCALE = 0.55;

export function ShaderBackground({ className = '' }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const gl = canvas?.getContext('webgl', { antialias: false, premultipliedAlpha: false });
    if (!canvas || !gl) return; // no WebGL: the CSS background behind it stays

    const compile = (type: number, src: string) => {
      const s = gl.createShader(type)!;
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };
    const program = gl.createProgram()!;
    gl.attachShader(program, compile(gl.VERTEX_SHADER, VERT));
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(program);
    gl.useProgram(program);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(program, 'a_position');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform3fv(gl.getUniformLocation(program, 'u_colors'), new Float32Array(COLORS.flat()));
    const uScene = gl.getUniformLocation(program, 'u_scene');
    const uCursor = gl.getUniformLocation(program, 'u_cursor');

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const start = performance.now();
    let raf = 0;
    let visible = true;
    const pointer = { x: 0, y: 0, tx: 0, ty: 0, presence: 0, target: 0 };

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const scale = Math.min(1, Math.sqrt(1_200_000 / Math.max(1, r.width * r.height * dpr * dpr)));
      canvas.width = Math.max(1, Math.round(r.width * dpr * scale));
      canvas.height = Math.max(1, Math.round(r.height * dpr * scale));
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    const draw = (now: number) => {
      raf = 0;
      pointer.x += (pointer.tx - pointer.x) * 0.08;
      pointer.y += (pointer.ty - pointer.y) * 0.08;
      pointer.presence += (pointer.target - pointer.presence) * 0.06;
      gl.uniform3f(uScene, canvas.width, canvas.height, reduced ? 4 : ((now - start) / 1000) * TIME_SCALE);
      gl.uniform4f(uCursor, pointer.x, pointer.y, reduced ? 0 : pointer.presence, 0.7);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      if (!reduced && visible && document.visibilityState === 'visible') raf = requestAnimationFrame(draw);
    };
    const kick = () => {
      if (!raf) raf = requestAnimationFrame(draw);
    };

    const onPointer = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect();
      const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
      pointer.target = inside ? 1 : 0;
      pointer.tx = ((e.clientX - r.left) / r.width) * 2 - 1;
      pointer.ty = -(((e.clientY - r.top) / r.height) * 2 - 1);
    };
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
      if (visible) kick();
    });
    const resizeObserver = new ResizeObserver(() => {
      resize();
      kick();
    });
    observer.observe(canvas);
    resizeObserver.observe(canvas);
    window.addEventListener('pointermove', onPointer, { passive: true });
    document.addEventListener('visibilitychange', kick);
    resize();
    kick();

    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
      resizeObserver.disconnect();
      window.removeEventListener('pointermove', onPointer);
      document.removeEventListener('visibilitychange', kick);
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    };
  }, []);

  return <canvas ref={ref} aria-hidden className={`block h-full w-full ${className}`} />;
}

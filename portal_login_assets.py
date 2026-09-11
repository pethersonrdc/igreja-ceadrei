"""Assets embutidos do login do Portal (não dependem do disco/Nginx)."""

from __future__ import annotations

import base64
from pathlib import Path

PORTAL_LOGIN_CSS = r"""/* ---------- Portal login (fundo Bíblia / fogo) ---------- */

body.tema-portal-login {
  min-height: 100vh;
  background: #0a0604 !important;
  color: #f0d78c;
}

body.tema-portal-login .site-header {
  background: rgba(8, 5, 3, 0.55);
  border-color: rgba(212, 175, 55, 0.28);
  backdrop-filter: blur(12px);
}

body.tema-portal-login .brand,
body.tema-portal-login .site-nav a {
  color: #f0d78c;
}

body.tema-portal-login .site-nav a:hover {
  color: #0a0604;
  background: #e0b35a;
}

body.tema-portal-login .site-footer {
  background: rgba(8, 5, 3, 0.72);
  border-top: 1px solid rgba(212, 175, 55, 0.22);
  color: rgba(240, 215, 140, 0.82);
}

body.tema-portal-login .footer-brand,
body.tema-portal-login .footer-lema,
body.tema-portal-login .footer-copy {
  color: rgba(240, 215, 140, 0.88);
}

body.tema-portal-login .fundo-pagina.fundo-pagina--portal {
  background-color: #0a0604;
  background-image: url("/portal/assets/fundo.jpg");
  background-size: cover;
  background-position: center 28%;
  background-repeat: no-repeat;
}

body.tema-portal-login .fundo-pagina--portal .fundo-pagina-img {
  object-fit: cover;
  object-position: center 28%;
  transform: scale(1.04);
  animation: portal-bg-breathe 14s ease-in-out infinite alternate;
}

body.tema-portal-login .fundo-pagina--portal::after {
  background:
    radial-gradient(ellipse 70% 55% at 50% 42%, rgba(255, 120, 20, 0.18), transparent 62%),
    linear-gradient(180deg, rgba(6, 3, 2, 0.55) 0%, rgba(6, 3, 2, 0.22) 38%, rgba(6, 3, 2, 0.72) 100%);
  display: block;
}

.portal-login-ember {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: radial-gradient(circle, #ffe08a 0%, #ff7a1a 55%, transparent 70%);
  box-shadow: 0 0 12px rgba(255, 140, 30, 0.85);
  opacity: 0;
  z-index: 1;
  animation: portal-ember-rise 5.5s ease-in infinite;
}

.portal-login-ember--1 { left: 18%; bottom: 12%; animation-delay: 0s; }
.portal-login-ember--2 { left: 38%; bottom: 8%; animation-delay: 1.1s; width: 4px; height: 4px; }
.portal-login-ember--3 { left: 52%; bottom: 14%; animation-delay: 2.2s; }
.portal-login-ember--4 { left: 66%; bottom: 10%; animation-delay: 0.7s; width: 5px; height: 5px; }
.portal-login-ember--5 { left: 78%; bottom: 16%; animation-delay: 3.1s; width: 4px; height: 4px; }

@keyframes portal-ember-rise {
  0% { opacity: 0; transform: translateY(0) scale(0.7); }
  15% { opacity: 0.95; }
  100% { opacity: 0; transform: translateY(-58vh) scale(0.2); }
}

@keyframes portal-bg-breathe {
  from { transform: scale(1.02); }
  to { transform: scale(1.07); }
}

.portal-login-wrap {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  min-height: calc(100vh - 11rem);
  max-width: 440px;
  margin-inline: auto;
  padding: 2rem 1rem 3rem;
}

.portal-login-card {
  width: min(100%, 400px);
  padding: 1.75rem 1.5rem 1.6rem;
  border-radius: 22px;
  background: rgba(10, 6, 4, 0.38);
  border: 1px solid rgba(232, 197, 106, 0.42);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.04) inset,
    0 24px 60px rgba(0, 0, 0, 0.45),
    0 0 40px rgba(255, 120, 20, 0.12);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  color: #f0d78c;
  animation: portal-card-in 0.9s cubic-bezier(0.22, 1, 0.36, 1) both;
  transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
}

.portal-login-card:hover {
  transform: translateY(-4px);
  border-color: rgba(240, 215, 140, 0.65);
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.06) inset,
    0 28px 70px rgba(0, 0, 0, 0.5),
    0 0 48px rgba(255, 140, 30, 0.2);
}

.portal-login-card.is-sending {
  animation: portal-card-pulse 0.7s ease;
  pointer-events: none;
  opacity: 0.92;
}

.portal-login-card.is-sending .portal-login-btn-glow {
  opacity: 1;
  animation: portal-btn-flare 0.7s ease;
}

@keyframes portal-card-in {
  from { opacity: 0; transform: translateY(28px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes portal-card-pulse {
  0%, 100% { transform: scale(1); }
  40% { transform: scale(0.985); }
  70% { transform: scale(1.01); }
}

.portal-login-brand {
  text-align: center;
  margin-bottom: 1.35rem;
}

.portal-login-emblema {
  width: 88px;
  height: 88px;
  margin: 0 auto 0.85rem;
  object-fit: contain;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.25);
  box-shadow:
    0 0 0 2px rgba(232, 197, 106, 0.55),
    0 0 28px rgba(255, 160, 40, 0.45);
  animation: portal-emblema-glow 2.8s ease-in-out infinite alternate;
}

@keyframes portal-emblema-glow {
  from {
    transform: scale(1);
    box-shadow: 0 0 0 2px rgba(232, 197, 106, 0.45), 0 0 18px rgba(255, 140, 30, 0.3);
  }
  to {
    transform: scale(1.05);
    box-shadow: 0 0 0 3px rgba(240, 215, 140, 0.7), 0 0 36px rgba(255, 170, 50, 0.65);
  }
}

.portal-login-eyebrow {
  margin: 0;
  font-size: 0.78rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #e8c56a;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.65);
}

.portal-login-title {
  margin: 0.35rem 0 0.4rem;
  font-family: var(--font-display);
  font-size: clamp(1.7rem, 4vw, 2.15rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #f5e2a3;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.7), 0 0 24px rgba(255, 150, 40, 0.25);
}

.portal-login-lead {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.45;
  color: rgba(240, 215, 140, 0.86);
  text-shadow: 0 1px 10px rgba(0, 0, 0, 0.55);
}

.portal-login-label {
  display: block;
  margin: 0.85rem 0 0.35rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: #e8c56a;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.5);
}

.portal-login-input {
  width: 100%;
  padding: 0.72rem 0.9rem;
  border-radius: 12px;
  border: 1px solid rgba(232, 197, 106, 0.55);
  background: rgba(255, 248, 230, 0.1);
  color: #fff4d0;
  font: inherit;
  outline: none;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}

.portal-login-input::placeholder {
  color: rgba(240, 215, 140, 0.45);
}

.portal-login-input:focus {
  border-color: #f0d78c;
  background: rgba(255, 248, 230, 0.16);
  box-shadow: 0 0 0 3px rgba(224, 179, 90, 0.28), 0 0 20px rgba(255, 140, 30, 0.18);
}

.portal-login-erro {
  margin: 0.85rem 0 0;
  padding: 0.55rem 0.75rem;
  border-radius: 10px;
  border: 1px solid rgba(255, 120, 90, 0.45);
  background: rgba(80, 10, 10, 0.45);
  color: #ffc9b8;
  font-size: 0.9rem;
}

.portal-login-btn {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 1.25rem;
  padding: 0.8rem 1.2rem;
  border: 1px solid rgba(240, 215, 140, 0.65);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(184, 130, 40, 0.85), rgba(120, 70, 18, 0.9));
  color: #fff6d8;
  font: inherit;
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.45);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35), 0 0 22px rgba(255, 140, 30, 0.25);
  transition: transform 0.28s ease, box-shadow 0.28s ease, filter 0.28s ease;
}

.portal-login-btn:hover {
  transform: translateY(-2px);
  filter: brightness(1.08);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.4), 0 0 30px rgba(255, 160, 40, 0.4);
}

.portal-login-btn:active {
  transform: translateY(0);
}

.portal-login-btn-text {
  position: relative;
  z-index: 1;
}

.portal-login-btn-glow {
  position: absolute;
  inset: -40%;
  background: linear-gradient(120deg, transparent 30%, rgba(255, 240, 180, 0.45) 50%, transparent 70%);
  opacity: 0;
  transform: translateX(-40%);
  pointer-events: none;
}

@keyframes portal-btn-flare {
  0% { opacity: 0; transform: translateX(-50%); }
  35% { opacity: 1; }
  100% { opacity: 0; transform: translateX(50%); }
}

@media (max-width: 640px) {
  .portal-login-wrap {
    min-height: calc(100vh - 9rem);
    padding-top: 1.25rem;
  }

  body.tema-portal-login .fundo-pagina--portal .fundo-pagina-img {
    object-position: center 22%;
  }
}

@media (prefers-reduced-motion: reduce) {
  body.tema-portal-login .fundo-pagina--portal .fundo-pagina-img,
  .portal-login-ember,
  .portal-login-emblema,
  .portal-login-card,
  .portal-login-btn-glow {
    animation: none !important;
  }
}
"""

_FUNDO_B64 = """
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
8F7ix9Rshhnz8eP/2Q==
""".replace("\n", "").replace(" ", "")

PORTAL_LOGIN_FUNDO_JPG = base64.b64decode(_FUNDO_B64)


def ensure_portal_login_files(static_folder: str | Path) -> None:
    """Grava CSS/fundo em static/ se faltarem (ajuda Nginx e deploys incompletos)."""
    root = Path(static_folder)
    css_path = root / "css" / "portal-login.css"
    img_path = root / "images" / "fundo-portal-login.jpg"
    img_alt = root / "images" / "portal" / "fundo-login.jpg"
    try:
        css_path.parent.mkdir(parents=True, exist_ok=True)
        img_path.parent.mkdir(parents=True, exist_ok=True)
        img_alt.parent.mkdir(parents=True, exist_ok=True)
        if not css_path.is_file() or css_path.stat().st_size < 100:
            css_path.write_text(PORTAL_LOGIN_CSS, encoding="utf-8")
        if not img_path.is_file() or img_path.stat().st_size < 1000:
            img_path.write_bytes(PORTAL_LOGIN_FUNDO_JPG)
        if not img_alt.is_file() or img_alt.stat().st_size < 1000:
            img_alt.write_bytes(PORTAL_LOGIN_FUNDO_JPG)
    except OSError:
        # Sem permissão de escrita: rotas em memória ainda funcionam.
        pass

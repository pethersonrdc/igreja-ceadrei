/**
 * Compartilha a escala como card (imagem), no estilo da Mensagem do Dia.
 * Botão: .js-escala-share com data-payload (JSON).
 */
(function () {
  function parsePayload(btn) {
    var raw = btn.getAttribute("data-payload") || "";
    try {
      return JSON.parse(raw);
    } catch (err) {
      return null;
    }
  }

  function mostrarHint(el, msg) {
    if (!el) return;
    el.hidden = false;
    el.textContent = msg;
  }

  function wrapText(ctx, text, x, y, maxWidth, lineHeight, align) {
    var words = String(text || "").split(/\s+/);
    var line = "";
    var lines = [];
    for (var i = 0; i < words.length; i++) {
      var test = line ? line + " " + words[i] : words[i];
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = words[i];
      } else {
        line = test;
      }
    }
    if (line) lines.push(line);
    ctx.textAlign = align || "center";
    lines.forEach(function (l, idx) {
      ctx.fillText(l, x, y + idx * lineHeight);
    });
    return lines.length;
  }

  function loadImage(src) {
    return new Promise(function (resolve) {
      if (!src) {
        resolve(null);
        return;
      }
      var img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        resolve(img);
      };
      img.onerror = function () {
        resolve(null);
      };
      img.src = src;
    });
  }

  function desenharCard(payload) {
    var canvas = document.createElement("canvas");
    canvas.width = 1080;
    canvas.height = 1350;
    var ctx = canvas.getContext("2d");
    var w = canvas.width;
    var h = canvas.height;

    var grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "#1a1208");
    grad.addColorStop(0.5, "#0c0905");
    grad.addColorStop(1, "#14100a");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    var glow = ctx.createRadialGradient(w / 2, 180, 30, w / 2, 180, 380);
    glow.addColorStop(0, "rgba(212, 160, 64, 0.32)");
    glow.addColorStop(1, "transparent");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, w, h);

    return loadImage(payload.logo).then(function (logo) {
      if (logo) {
        var size = 110;
        ctx.save();
        ctx.beginPath();
        ctx.arc(w / 2, 120, size / 2, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(logo, w / 2 - size / 2, 120 - size / 2, size, size);
        ctx.restore();
      }

      ctx.fillStyle = "#e0b35a";
      ctx.font = "600 28px Georgia, serif";
      ctx.textAlign = "center";
      ctx.fillText((payload.eyebrow || "ESCALA DOS OBREIROS").toUpperCase(), w / 2, 220);

      ctx.fillStyle = "#fff8ee";
      ctx.font = "700 54px Georgia, serif";
      wrapText(ctx, payload.igreja || "IGREJA CEASDREI", w / 2, 290, 900, 58);

      ctx.fillStyle = "#f0c75e";
      ctx.font = "600 36px Georgia, serif";
      ctx.fillText(payload.data || "", w / 2, 390);

      var boxTop = 460;
      var boxH = 560;
      ctx.fillStyle = "rgba(255, 248, 238, 0.08)";
      ctx.strokeStyle = "rgba(224, 179, 90, 0.45)";
      ctx.lineWidth = 2;
      roundRect(ctx, 90, boxTop, w - 180, boxH, 28);
      ctx.fill();
      ctx.stroke();

      var linhas = payload.linhas || [];
      var y = boxTop + 90;
      linhas.forEach(function (item) {
        ctx.fillStyle = "#e0b35a";
        ctx.font = "600 24px Arial, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(String(item.label || "").toUpperCase(), w / 2, y);
        ctx.fillStyle = "#fff8ee";
        ctx.font = "600 34px Georgia, serif";
        var used = wrapText(ctx, item.valor || "—", w / 2, y + 48, 820, 40);
        y += 70 + used * 40;
      });

      ctx.fillStyle = "rgba(255, 248, 238, 0.7)";
      ctx.font = "400 24px Arial, sans-serif";
      ctx.fillText(payload.rodape || "Uma casa de oração, comunhão e esperança", w / 2, h - 80);

      return new Promise(function (resolve) {
        canvas.toBlob(function (blob) {
          if (blob) resolve(blob);
          else resolve(null);
        }, "image/png");
      });
    });
  }

  function roundRect(ctx, x, y, width, height, radius) {
    var r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + width, y, x + width, y + height, r);
    ctx.arcTo(x + width, y + height, x, y + height, r);
    ctx.arcTo(x, y + height, x, y, r);
    ctx.arcTo(x, y, x + width, y, r);
    ctx.closePath();
  }

  function baixarBlob(blob, nome) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = nome;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1500);
  }

  function bindButton(btn) {
    var hint = document.querySelector(btn.getAttribute("data-hint") || ".escala-share-hint");
    btn.addEventListener("click", function () {
      var payload = parsePayload(btn);
      if (!payload) {
        mostrarHint(hint, "Não foi possível montar a escala.");
        return;
      }
      mostrarHint(hint, "Gerando o card da escala...");
      desenharCard(payload)
        .then(function (blob) {
          if (!blob) throw new Error("blob");
          var file = new File([blob], "escala-obreiros-ceasdrei.png", { type: "image/png" });
          var texto = payload.texto || "";
          if (navigator.canShare && navigator.canShare({ files: [file] })) {
            return navigator
              .share({
                files: [file],
                title: (payload.igreja || "IGREJA CEASDREI") + " — Escala",
                text: texto,
              })
              .then(function () {
                mostrarHint(hint, "Card da escala compartilhado.");
              });
          }
          baixarBlob(blob, "escala-obreiros-ceasdrei.png");
          if (texto) {
            window.open(
              "https://wa.me/?text=" + encodeURIComponent(texto),
              "_blank",
              "noopener,noreferrer"
            );
          }
          mostrarHint(
            hint,
            "Card baixado. No WhatsApp, anexe a imagem para enviar a escala completa."
          );
        })
        .catch(function () {
          if (payload.texto) {
            window.open(
              "https://wa.me/?text=" + encodeURIComponent(payload.texto),
              "_blank",
              "noopener,noreferrer"
            );
            mostrarHint(hint, "Abrindo WhatsApp com o texto da escala.");
          } else {
            mostrarHint(hint, "Não foi possível gerar o card. Tente novamente.");
          }
        });
    });
  }

  document.querySelectorAll(".js-escala-share").forEach(bindButton);
})();

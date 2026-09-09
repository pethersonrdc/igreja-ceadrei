/**
 * Compartilha o assento do ônibus como card (imagem), no estilo da Mensagem do Dia.
 * Botão: .js-onibus-share com data-payload (JSON: numero, nome, igreja, logo, link, texto).
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

  function desenharCard(payload) {
    var canvas = document.createElement("canvas");
    canvas.width = 1080;
    canvas.height = 1350;
    var ctx = canvas.getContext("2d");
    var w = canvas.width;
    var h = canvas.height;

    var grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "#1a1208");
    grad.addColorStop(0.45, "#0a0704");
    grad.addColorStop(1, "#120c06");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    var glow = ctx.createRadialGradient(w / 2, h * 0.22, 40, w / 2, h * 0.22, 420);
    glow.addColorStop(0, "rgba(212, 160, 64, 0.35)");
    glow.addColorStop(1, "transparent");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, w, h);

    return loadImage(payload.logo).then(function (logo) {
      if (logo) {
        var size = 140;
        ctx.drawImage(logo, (w - size) / 2, 90, size, size);
      }

      ctx.fillStyle = "rgba(255, 248, 238, 0.75)";
      ctx.font = "600 28px Georgia, 'Times New Roman', serif";
      ctx.textAlign = "center";
      ctx.fillText("EVENTO BATISMO", w / 2, 280);

      ctx.fillStyle = "#fff8ee";
      ctx.font = "700 52px Georgia, 'Times New Roman', serif";
      ctx.fillText("Assento do ônibus", w / 2, 350);

      var boxX = 90;
      var boxY = 420;
      var boxW = w - 180;
      var boxH = 520;
      ctx.fillStyle = "#c9a24d";
      roundRect(ctx, boxX, boxY, boxW, boxH, 28);
      ctx.fill();

      ctx.fillStyle = "#2a1c0c";
      ctx.font = "600 30px Arial, sans-serif";
      ctx.fillText("ASSENTO", w / 2, boxY + 110);

      ctx.fillStyle = "#1a1208";
      ctx.font = "700 120px Georgia, 'Times New Roman', serif";
      ctx.fillText(String(payload.numero || "—"), w / 2, boxY + 250);

      ctx.fillStyle = "#1a1208";
      ctx.font = "700 44px Georgia, 'Times New Roman', serif";
      wrapText(ctx, payload.nome || "—", w / 2, boxY + 340, boxW - 100, 52);

      ctx.fillStyle = "#2a1c0c";
      ctx.font = "600 28px Arial, sans-serif";
      ctx.fillText("Confirmado no site", w / 2, boxY + boxH - 60);

      ctx.fillStyle = "#f0c75e";
      ctx.font = "700 36px Georgia, 'Times New Roman', serif";
      ctx.fillText(payload.igreja || "IGREJA CEASDREI", w / 2, 1060);

      var link = String(payload.link || "").replace(/^https?:\/\//, "");
      ctx.fillStyle = "rgba(255, 248, 238, 0.78)";
      ctx.font = "400 26px Arial, sans-serif";
      ctx.fillText(link || "Escala do ônibus no site", w / 2, 1115);

      return new Promise(function (resolve) {
        canvas.toBlob(function (blob) {
          resolve(blob || null);
        }, "image/png");
      });
    });
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
    var hint = document.querySelector(btn.getAttribute("data-hint") || ".onibus-share-hint");
    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      var payload = parsePayload(btn);
      if (!payload) {
        mostrarHint(hint, "Não foi possível montar o card do assento.");
        return;
      }
      mostrarHint(hint, "Gerando o card do assento...");
      desenharCard(payload)
        .then(function (blob) {
          if (!blob) throw new Error("blob");
          var num = payload.numero || "assento";
          var fileName = "assento-" + num + "-ceasdrei.png";
          var file = new File([blob], fileName, { type: "image/png" });
          var texto = payload.texto || "";
          if (navigator.canShare && navigator.canShare({ files: [file] })) {
            return navigator
              .share({
                files: [file],
                title: (payload.igreja || "IGREJA CEASDREI") + " — Assento " + num,
                text: texto,
              })
              .then(function () {
                mostrarHint(hint, "Card do assento compartilhado.");
              });
          }
          baixarBlob(blob, fileName);
          if (texto) {
            window.open(
              "https://wa.me/?text=" + encodeURIComponent(texto),
              "_blank",
              "noopener,noreferrer"
            );
          }
          mostrarHint(
            hint,
            "Card baixado. No WhatsApp, anexe a imagem do assento para enviar."
          );
        })
        .catch(function () {
          if (payload.texto) {
            window.open(
              "https://wa.me/?text=" + encodeURIComponent(payload.texto),
              "_blank",
              "noopener,noreferrer"
            );
            mostrarHint(hint, "Abrindo WhatsApp com o texto do assento.");
          } else {
            mostrarHint(hint, "Não foi possível gerar o card. Tente novamente.");
          }
        });
    });
  }

  document.querySelectorAll(".js-onibus-share").forEach(bindButton);
})();

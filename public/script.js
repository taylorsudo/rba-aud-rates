(() => {
  "use strict";

  const HISTORY_URL = "./history.json";

  const THEME = {
    line: "#667eea",
    marker: "#764ba2",
    markerBorder: "#ffffff",
    titleText: "#1a202c",
    gridColor: "#e2e8f0",
    axisLine: "#cbd5e0",
    plotBg: "#f7fafc",
    paperBg: "#ffffff",
    hoverBg: "#1a202c",
    error: "#e53e3e",
  };

  const FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

  const CHART_CONFIG = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
  };

  let history = [];

  function showMessage(text, color = THEME.error) {
    document.getElementById("chart").innerHTML =
      `<p style="color: ${color}; padding: 20px;">${text}</p>`;
  }

  function computeSeries(code) {
    const x = [];
    const y = [];
    for (const day of history) {
      const found = (day.rates || []).find(r => r.code === code);
      if (found && typeof found.aud_per_unit === "number") {
        x.push(day.date || "");
        y.push(found.aud_per_unit);
      }
    }
    console.log(`Series for ${code}: ${x.length} data points`);
    return { x, y };
  }

  function buildTrace(code, x, y) {
    return {
      x,
      y,
      mode: "lines+markers",
      name: code,
      line: {
        color: THEME.line,
        width: 3,
        shape: "spline",
      },
      marker: {
        color: THEME.marker,
        size: 8,
        line: {
          color: THEME.markerBorder,
          width: 2,
        },
      },
    };
  }

  function buildLayout(code, y) {
    const yMin = Math.min(...y);
    const yMax = Math.max(...y);
    const padding = (yMax - yMin) * 0.1; // 10% padding for readability

    return {
      title: {
        text: `${code} to AUD Exchange Rate`,
        font: { size: 20, color: THEME.titleText, family: FONT_FAMILY },
      },
      xaxis: {
        title: "Date",
        gridcolor: THEME.gridColor,
        showline: true,
        linecolor: THEME.axisLine,
        type: "date",
      },
      yaxis: {
        title: `AUD per 1 ${code}`,
        range: [yMin - padding, yMax + padding],
        gridcolor: THEME.gridColor,
        showline: true,
        linecolor: THEME.axisLine,
      },
      plot_bgcolor: THEME.plotBg,
      paper_bgcolor: THEME.paperBg,
      margin: { t: 60, r: 40, b: 60, l: 60 },
      hovermode: "closest",
      hoverlabel: { bgcolor: THEME.hoverBg, font: { color: "white", size: 13 } },
    };
  }

  function render(code) {
    const { x, y } = computeSeries(code);

    if (x.length === 0) {
      showMessage(`No data available for ${code}`);
      return;
    }

    Plotly.newPlot("chart", [buildTrace(code, x, y)], buildLayout(code, y), CHART_CONFIG);
  }

  function collectCodes() {
    const set = new Set();
    for (const day of history) {
      for (const r of day.rates || []) set.add(r.code);
    }
    return Array.from(set).sort();
  }

  function populateCodes() {
    const codes = collectCodes();
    console.log(`Found ${codes.length} currency codes:`, codes);

    const sel = document.getElementById("codeSel");
    sel.innerHTML = codes.map(c => `<option value="${c}">${c}</option>`).join("");
    sel.value = codes.includes("USD") ? "USD" : codes[0];
    sel.addEventListener("change", () => render(sel.value));
    render(sel.value);
  }

  function init() {
    fetch(HISTORY_URL, { cache: "no-store" })
      .then(r => {
        if (!r.ok) {
          throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }
        return r.json();
      })
      .then(data => {
        console.log(`Loaded ${data.length} days of history`);
        history = data;
        populateCodes();
      })
      .catch(err => {
        showMessage(`Failed to load data: ${err.message}`);
        console.error("Fetch error:", err);
      });
  }

  init();
})();

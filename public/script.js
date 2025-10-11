const HISTORY_URL = "./history.json";

let history = [];
let codes = [];

function computeSeries(code) {
    const x = [];
    const y = [];
    for (const day of history) {
        const d = day.date || "";
        const found = (day.rates || []).find(r => r.code === code);
        if (found && typeof found.aud_per_unit === "number") {
            x.push(d);
            y.push(found.aud_per_unit);
        }
    }
    console.log(`Series for ${code}: ${x.length} data points`);
    return { x, y };
}

function render(code) {
    const { x, y } = computeSeries(code);

    if (x.length === 0) {
        document.getElementById("chart").innerHTML = 
            `<p style="color: #e53e3e; padding: 20px;">No data available for ${code}</p>`;
        return;
    }

    const trace = {
        x,
        y,
        mode: "lines+markers",
        name: code,
        line: {
            color: '#667eea',
            width: 3,
            shape: 'spline'
        },
        marker: {
            color: '#764ba2',
            size: 8,
            line: {
                color: 'white',
                width: 2
            }
        }
    };

    const layout = {
        title: {
            text: `${code} to AUD Exchange Rate`,
            font: {
                size: 20,
                color: '#1a202c',
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            }
        },
        xaxis: {
            title: "Date",
            gridcolor: '#e2e8f0',
            showline: true,
            linecolor: '#cbd5e0',
            type: 'date'  // Explicitly set date type
        },
        yaxis: {
            title: `AUD per 1 ${code}`,
            gridcolor: '#e2e8f0',
            showline: true,
            linecolor: '#cbd5e0'
        },
        plot_bgcolor: '#f7fafc',
        paper_bgcolor: 'white',
        margin: { t: 60, r: 40, b: 60, l: 60 },
        hovermode: 'closest',
        hoverlabel: {
            bgcolor: '#1a202c',
            font: { color: 'white', size: 13 }
        }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    Plotly.newPlot("chart", [trace], layout, config);
}

function populateCodes() {
    const set = new Set();
    for (const day of history) {
        for (const r of (day.rates || [])) set.add(r.code);
    }
    codes = Array.from(set).sort();

    console.log(`Found ${codes.length} currency codes:`, codes);

    const sel = document.getElementById("codeSel");
    sel.innerHTML = codes.map(c => `<option value="${c}">${c}</option>`).join("");
    sel.value = codes.includes("USD") ? "USD" : codes[0];
    sel.addEventListener("change", () => render(sel.value));
    render(sel.value);
}

fetch(HISTORY_URL, { cache: "no-store" })
    .then(r => {
        if (!r.ok) {
            throw new Error(`HTTP ${r.status}: ${r.statusText}`);
        }
        return r.json();
    })
    .then(j => {
        console.log(`Loaded ${j.length} days of history`);
        history = j;
        populateCodes();
    })
    .catch(err => {
        document.getElementById("chart").innerHTML =
            `<p style="color: #e53e3e; padding: 20px;">Failed to load data: ${err.message}</p>`;
        console.error('Fetch error:', err);
    });
// IR Vibrational Widget - Frontend
// Displays IR frequency table and spectrum plot

function render({ model, el }) {
  // Main container
  const container = document.createElement("div");
  container.className = "ir-widget-container";
  
  // Error display
  const errorDiv = document.createElement("div");
  errorDiv.className = "ir-error";
  
  // Table container
  const tableContainer = document.createElement("div");
  tableContainer.className = "ir-table-container";
  
  // Plot container
  const plotContainer = document.createElement("div");
  plotContainer.className = "ir-plot-container";
  
  // Canvas for plotting
  const canvas = document.createElement("canvas");
  canvas.className = "ir-plot-canvas";
  plotContainer.appendChild(canvas);
  
  container.appendChild(errorDiv);
  container.appendChild(tableContainer);
  container.appendChild(plotContainer);
  el.appendChild(container);
  
  // Rendering functions
  function renderError() {
    const error = model.get("error_message");
    if (error) {
      errorDiv.textContent = error;
      errorDiv.style.display = "block";
    } else {
      errorDiv.style.display = "none";
    }
  }
  
  function renderTable() {
    const showTable = model.get("show_table");
    const data = model.get("data");
    
    if (!showTable || !data.modes || data.modes.length === 0) {
      tableContainer.style.display = "none";
      return;
    }
    
    tableContainer.style.display = "block";
    
    // Create table
    let html = '<div class="ir-table-header">';
    if (data.formula) {
      html += `<h3>IR Vibrational Frequencies - ${data.formula}</h3>`;
    } else {
      html += '<h3>IR Vibrational Frequencies</h3>';
    }
    html += `<p>${data.n_modes} normal modes</p>`;
    html += '</div>';
    
    html += '<table class="ir-table">';
    html += '<thead><tr>';
    html += '<th class="sortable" data-column="mode">Mode #</th>';
    html += '<th class="sortable" data-column="frequency">Frequency (cm⁻¹)</th>';
    html += '<th class="sortable" data-column="intensity">Intensity (km/mol)</th>';
    html += '</tr></thead>';
    html += '<tbody>';
    
    for (const mode of data.modes) {
      html += '<tr>';
      html += `<td>${mode.mode}</td>`;
      html += `<td>${mode.frequency.toFixed(2)}</td>`;
      html += `<td>${mode.intensity.toFixed(4)}</td>`;
      html += '</tr>';
    }
    
    html += '</tbody></table>';
    tableContainer.innerHTML = html;
    
    // Add sorting functionality
    const headers = tableContainer.querySelectorAll("th.sortable");
    headers.forEach(header => {
      header.addEventListener("click", () => {
        const column = header.dataset.column;
        sortTable(column);
      });
    });
  }
  
  let sortColumn = null;
  let sortAscending = true;
  
  function sortTable(column) {
    const data = model.get("data");
    if (!data.modes) return;
    
    // Toggle sort direction if same column
    if (sortColumn === column) {
      sortAscending = !sortAscending;
    } else {
      sortColumn = column;
      sortAscending = true;
    }
    
    // Sort modes
    const sortedModes = [...data.modes].sort((a, b) => {
      const valA = a[column];
      const valB = b[column];
      return sortAscending ? valA - valB : valB - valA;
    });
    
    // Update table body
    const tbody = tableContainer.querySelector("tbody");
    tbody.innerHTML = "";
    
    for (const mode of sortedModes) {
      const row = tbody.insertRow();
      row.insertCell().textContent = mode.mode;
      row.insertCell().textContent = mode.frequency.toFixed(2);
      row.insertCell().textContent = mode.intensity.toFixed(4);
    }
    
    // Update sort indicators
    tableContainer.querySelectorAll("th.sortable").forEach(th => {
      th.classList.remove("sort-asc", "sort-desc");
    });
    const header = tableContainer.querySelector(`th[data-column="${column}"]`);
    header.classList.add(sortAscending ? "sort-asc" : "sort-desc");
  }
  
  function renderPlot() {
    const showPlot = model.get("show_plot");
    const data = model.get("data");
    
    if (!showPlot || !data.modes || data.modes.length === 0) {
      plotContainer.style.display = "none";
      return;
    }
    
    plotContainer.style.display = "block";
    
    const ctx = canvas.getContext("2d");
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    
    // Set canvas resolution
    canvas.width = width * 2;
    canvas.height = height * 2;
    ctx.scale(2, 2);
    
    // Get parameters
    const xMin = model.get("x_min");
    const xMax = model.get("x_max");
    const broadening = model.get("broadening");
    const fwhm = model.get("fwhm");
    
    // Margins
    const margin = { top: 20, right: 20, bottom: 50, left: 60 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Calculate spectrum
    const spectrum = calculateSpectrum(data.modes, xMin, xMax, broadening, fwhm);
    
    // Find max intensity for scaling
    const maxIntensity = Math.max(...spectrum.map(p => p.y));
    
    // Draw axes
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top);
    ctx.lineTo(margin.left, margin.top + plotHeight);
    ctx.lineTo(margin.left + plotWidth, margin.top + plotHeight);
    ctx.stroke();
    
    // Draw spectrum
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    
    let firstPoint = true;
    for (const point of spectrum) {
      const x = margin.left + ((point.x - xMin) / (xMax - xMin)) * plotWidth;
      const y = margin.top + plotHeight - (point.y / maxIntensity) * plotHeight;
      
      if (firstPoint) {
        ctx.moveTo(x, y);
        firstPoint = false;
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
    
    // Draw axes labels
    ctx.fillStyle = "#333";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    
    // X-axis label
    ctx.fillText("Wavenumber (cm⁻¹)", width / 2, height - 10);
    
    // Y-axis label (rotated)
    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("Intensity", 0, 0);
    ctx.restore();
    
    // X-axis tick marks and labels
    const numTicks = 5;
    for (let i = 0; i <= numTicks; i++) {
      const value = xMin + (xMax - xMin) * (i / numTicks);
      const x = margin.left + (i / numTicks) * plotWidth;
      const y = margin.top + plotHeight;
      
      // Tick mark
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x, y + 5);
      ctx.stroke();
      
      // Label
      ctx.fillText(Math.round(value).toString(), x, y + 20);
    }
    
    // Y-axis tick marks (relative intensity)
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const value = i / 4;
      const x = margin.left;
      const y = margin.top + plotHeight - (i / 4) * plotHeight;
      
      // Tick mark
      ctx.beginPath();
      ctx.moveTo(x - 5, y);
      ctx.lineTo(x, y);
      ctx.stroke();
      
      // Label
      ctx.fillText((value * 100).toFixed(0) + "%", x - 10, y + 4);
    }
  }
  
  function calculateSpectrum(modes, xMin, xMax, broadening, fwhm) {
    const resolution = model.get("resolution");
    const numPoints = Math.ceil((xMax - xMin) * resolution);
    const spectrum = [];
    
    for (let i = 0; i < numPoints; i++) {
      const x = xMin + (i / numPoints) * (xMax - xMin);
      let y = 0;
      
      if (broadening === "none") {
        // Stick spectrum: only add intensity at exact frequency
        for (const mode of modes) {
          if (Math.abs(mode.frequency - x) < 0.5 / resolution) {
            y = Math.max(y, mode.intensity);
          }
        }
      } else {
        // Apply broadening
        for (const mode of modes) {
          if (broadening === "lorentzian") {
            y += lorentzian(x, mode.frequency, mode.intensity, fwhm);
          } else if (broadening === "gaussian") {
            y += gaussian(x, mode.frequency, mode.intensity, fwhm);
          }
        }
      }
      
      spectrum.push({ x, y });
    }
    
    return spectrum;
  }
  
  function lorentzian(x, x0, intensity, fwhm) {
    const gamma = fwhm / 2;
    return intensity * (gamma * gamma) / ((x - x0) * (x - x0) + gamma * gamma);
  }
  
  function gaussian(x, x0, intensity, fwhm) {
    const sigma = fwhm / (2 * Math.sqrt(2 * Math.log(2)));
    return intensity * Math.exp(-((x - x0) * (x - x0)) / (2 * sigma * sigma));
  }
  
  function update() {
    renderError();
    renderTable();
    renderPlot();
  }
  
  // Initial render
  update();
  
  // Watch for changes
  model.on("change:error_message", update);
  model.on("change:data", update);
  model.on("change:show_table", update);
  model.on("change:show_plot", update);
  model.on("change:broadening", update);
  model.on("change:fwhm", update);
  model.on("change:x_min", update);
  model.on("change:x_max", update);
  model.on("change:resolution", update);
  
  // Handle window resize
  const resizeObserver = new ResizeObserver(() => {
    renderPlot();
  });
  resizeObserver.observe(plotContainer);
}

export default { render };

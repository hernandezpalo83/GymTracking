/**
 * Funciones para renderizar gráficos con Chart.js
 * Requiere: Chart.js (https://cdn.jsdelivr.net/npm/chart.js)
 */

// Colores para los gráficos
const CHART_COLORS = {
    primary: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#06b6d4',
    purple: '#8b5cf6',
    pink: '#ec4899',
};

/**
 * Renderizar gráfico de línea (para Progreso Personal)
 */
function renderProgressChart(canvasId, labels, volumes) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volumen (kg)',
                data: volumes,
                borderColor: CHART_COLORS.primary,
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: CHART_COLORS.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' kg';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Renderizar gráfico de pastel (para Tipo de Ejercicio)
 */
function renderTypeChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    CHART_COLORS.primary,
                    CHART_COLORS.success,
                    CHART_COLORS.warning,
                    CHART_COLORS.danger,
                    CHART_COLORS.info,
                    CHART_COLORS.purple,
                ],
                borderColor: '#fff',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

/**
 * Renderizar gráfico de barras (para Grupo Muscular)
 */
function renderMuscleChart(canvasId, labels, volumes) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Volumen (kg)',
                data: volumes,
                backgroundColor: CHART_COLORS.primary,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                }
            }
        }
    });
}

/**
 * Renderizar medidor de performance
 */
function renderGaugeChart(canvasId, value) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;

    // Dibujar fondo
    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2 + 20, 60, Math.PI, 0);
    ctx.stroke();

    // Dibujar progreso
    const normalizedValue = value / 100;
    ctx.strokeStyle = getColorForScore(value);
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2 + 20, 60, Math.PI, Math.PI + Math.PI * normalizedValue);
    ctx.stroke();

    // Escribir número
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round(value), width / 2, height / 2);

    ctx.fillStyle = '#6b7280';
    ctx.font = '14px Arial';
    ctx.fillText('/100', width / 2, height / 2 + 30);
}

/**
 * Renderizar heatmap de consistencia
 */
function renderHeatmapChart(canvasId, dates, values) {
    const container = document.getElementById(canvasId);
    if (!container) return;

    // Crear HTML del heatmap
    let html = '<div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px;">';

    dates.forEach((date, index) => {
        const value = values[index] || 0;
        const color = value ? CHART_COLORS.success : '#e5e7eb';
        const title = date;

        html += `<div style="width:30px; height:30px; background:${color}; border-radius:4px; cursor:pointer;" title="${title}"></div>`;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Obtener color según score
 */
function getColorForScore(score) {
    if (score >= 80) return CHART_COLORS.success;
    if (score >= 60) return CHART_COLORS.warning;
    if (score >= 40) return CHART_COLORS.info;
    return CHART_COLORS.danger;
}

/**
 * Formatear número con separador de miles
 */
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
}

/**
 * Animar incremento de números
 */
function animateCounter(elementId, finalValue, duration = 1000) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const startValue = 0;
    const startTime = Date.now();

    function update() {
        const now = Date.now();
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentValue = Math.floor(startValue + (finalValue - startValue) * progress);

        element.textContent = formatNumber(currentValue);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    update();
}

/**
 * Exportar gráfico a PNG
 */
function exportChartAsPNG(canvasId, fileName) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = fileName || 'grafico.png';
    link.href = canvas.toDataURL();
    link.click();
}

/**
 * Inicializar tooltips (requiere Popper.js y Tooltip.js)
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
});

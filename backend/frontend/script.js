
async function cargarDatos() {
    const response = await fetch('/datos');
    const data = await response.json();
    const contenedor = document.getElementById('datos');
    contenedor.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
}

async function predecir() {
    const response = await fetch('/predecir', {
        method: 'POST'
    });
    const result = await response.json();
    console.log(result);
    const contenedor = document.getElementById('predicciones');
    contenedor.innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
}

async function cargarKPIs() {
    try {
        const url = `/kpis?${obtenerParametros()}`;
        const response = await fetch(url);
        const data = await response.json();

        // Si no hay datos o promedio_volumen es null o NaN, resetear todo a cero
        if (!data || isNaN(data.promedio_volumen)) {
            document.getElementById('clientes').innerText = 0;
            document.getElementById('anomalias').innerText = 0;
            document.getElementById('alertas').innerText = 0;
            document.getElementById('volumen').innerText = '0 m³';
            document.getElementById('presion').innerText = '0 psi';
            document.getElementById('temperatura').innerText = '0 °C';
            return;
        }

        document.getElementById('clientes').innerText = data.total_clientes ?? 0;
        document.getElementById('anomalias').innerText = data.total_anomalias ?? 0;
        document.getElementById('alertas').innerText = data.alertas_criticas ?? 0;
        document.getElementById('volumen').innerText = (data.promedio_volumen ?? 0) + ' m³';
        document.getElementById('presion').innerText = (data.promedio_presion ?? 0) + ' psi';
        document.getElementById('temperatura').innerText = (data.promedio_temperatura ?? 0) + ' °C';
    } catch (error) {
        console.error('Error al cargar KPIs:', error);

        // En caso de error también limpiar KPIs para no mostrar datos viejos
        document.getElementById('clientes').innerText = 0;
        document.getElementById('anomalias').innerText = 0;
        document.getElementById('alertas').innerText = 0;
        document.getElementById('volumen').innerText = '0 m³';
        document.getElementById('presion').innerText = '0 psi';
        document.getElementById('temperatura').innerText = '0 °C';
    }
}
async function cargarGraficoConsumo() {
    try {
        const url = `/grafico_volumen?${obtenerParametros()}`;
        const response = await fetch(url);
        const data = await response.json();

        const ctx = document.getElementById('graficoConsumo').getContext('2d');
        if (window.myChart) window.myChart.destroy();

        window.myChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Volumen (m³)',
                    data: data.datos,
                    segment: {
                        borderColor: ctx => {
                            const riesgo = ctx.p0.raw?.riesgo;
                            if (riesgo === 'Alto') return '#e74c3c';      // rojo
                            if (riesgo === 'Medio') return '#f1c40f';     // amarillo
                            if (riesgo === 'Bajo') return '#2ecc71';      // verde
                            return '#95a5a6';                             // gris
                        }
                    },
		    borderColor: undefined,
                    pointBackgroundColor: data.datos.map(punto => {
                        if (punto.riesgo === 'Alto') return '#e74c3c';
                        if (punto.riesgo === 'Medio') return '#f1c40f';
                        if (punto.riesgo === 'Bajo') return '#2ecc71';
                        return '#95a5a6';
                    }),
                    backgroundColor: 'rgba(75, 192, 192, 0.2)', // solo fondo del área bajo la curva (opcional)
                    borderWidth: 2,
                    tension: 0.3,
                    parsing: {
                        xAxisKey: 'x',
                        yAxisKey: 'y'
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,   // <--- Aquí está el ajuste
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const punto = context.raw;
                                return [
                                    `Volumen: ${punto.y} m³`,
                                    `Presión: ${punto.presion} psi`,
                                    `Temperatura: ${punto.temperatura} °C`
                                ];
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Consumo Diario (Volumen, Presión, Temperatura)'
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        title: { display: true, text: 'Fecha' }
                    },
                    y: {
                        title: { display: true, text: 'Volumen (m³)' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al cargar gráfico de consumo:', error);
    }
}


async function cargarGraficoRiesgoCliente() {
    try {
        const url = `/riesgo_por_cliente?${obtenerParametros()}`;
        const response = await fetch(url);
        const data = await response.json();

        const clientes = data.clientes;
        const riesgos = data.riesgos;
        const valores = data.valores;

        const colores = ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6'];

        const datasets = riesgos.map((riesgo, i) => ({
            label: riesgo,
            data: clientes.map(cliente => valores[riesgo][clientes.indexOf(cliente)]),
            backgroundColor: colores[i % colores.length],
        }));

        const ctx = document.getElementById('graficoRiesgoCliente').getContext('2d');
        if (window.chartRiesgo) window.chartRiesgo.destroy();

        window.chartRiesgo = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: clientes,
                datasets: datasets
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribución de Riesgo por Cliente'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        title: { display: true, text: 'Cliente' }
                    },
                    y: {
                        stacked: true,
                        title: { display: true, text: 'Cantidad de registros' }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al cargar gráfico de riesgo:', error);
    }
}

window.cargarHeatmapAnomalias = async function() {
    try {
        const response = await fetch(`/anomalias_por_dia_hora?${obtenerParametros()}`);
        const data = await response.json();

        let dias = data.dias;
        const horas = data.horas;
        let matriz = data.matriz;

        if (!dias.length || !horas.length) {
            document.getElementById('heatmapAnomalias').style.display = 'none';
            document.getElementById('mensajeSinAnomalias').style.display = 'block';
            return;
        }

        // Padding visual para evitar superposición
        dias = ["", ...dias, ""];
        const filaVacia = new Array(horas.length).fill(0);
        matriz = [filaVacia, ...matriz, filaVacia];

        const valores = [];
        for (let i = 0; i < dias.length; i++) {
            for (let j = 0; j < horas.length; j++) {
                valores.push({ x: horas[j], y: dias[i], v: matriz[i][j] });
            }
        }

        const maxValue = Math.max(...matriz.flat());
        const canvas = document.getElementById('heatmapAnomalias');
        const existingChart = Chart.getChart(canvas);
        if (existingChart) existingChart.destroy();

        const ctx = canvas.getContext('2d');

        window.chartHeatmap = new Chart(ctx, {
            type: 'matrix',
            data: {
                datasets: [{
                    label: 'Anomalías',
                    data: valores,
                    backgroundColor: ctx => {
                        const v = ctx.raw.v;
                        const alpha = maxValue === 0 ? 0 : v / maxValue;
                        return `rgba(255, 99, 132, ${Math.min(alpha, 1)})`;
                    },
                    width: ctx => {
                        const area = ctx.chart.chartArea;
                        return area ? area.width / horas.length - 4 : 30;
                    },
                    height: ctx => {
                        const area = ctx.chart.chartArea;
                        return area ? area.width / horas.length - 4 : 30;
                    }, // o ajusta a lo que prefieras
                    borderWidth: 1,
                    borderColor: 'rgba(255,255,255,0.5)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Anomalías por Día y Hora'
                    },
                    tooltip: {
                        callbacks: {
                            label: ctx => `Día: ${ctx.raw.y}, Hora: ${ctx.raw.x}, Anomalías: ${ctx.raw.v}`
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'category',
                        labels: horas,
                        title: { display: true, text: 'Hora del Día' }
                    },
                    y: {
                        type: 'category',
                        labels: dias,
                        title: { display: true, text: 'Día de la Semana' }
                    }
                }
            }
        });

        document.getElementById('heatmapAnomalias').style.display = 'block';
        document.getElementById('mensajeSinAnomalias').style.display = 'none';

    } catch (error) {
        console.error('Error al cargar heatmap de anomalías:', error);
        document.getElementById('mensajeSinAnomalias').innerText = "Error al cargar anomalías.";
        document.getElementById('mensajeSinAnomalias').style.display = 'block';
        document.getElementById('heatmapAnomalias').style.display = 'none';
    }
};


async function cargarTablaRegistros() {
    try {
        const url = `/tabla_registros?${obtenerParametros()}`;
        const response = await fetch(url);
        const data = await response.json();

        const contenedor = document.getElementById('tabla-registros');
        if (!data || data.length === 0) {
            contenedor.innerHTML = '<p>No hay registros disponibles.</p>';
            return;
        }

        const cabecera = ['Fecha', 'Presion', 'Temperatura', 'Volumen', 'Volumen_Predicho', 'Residual', 'Riesgo'];

        let html = '<table border="1" cellpadding="6" cellspacing="0"><thead><tr>';
        cabecera.forEach(col => {
            html += `<th>${col}</th>`;
        });
        html += '</tr></thead><tbody>';

        data.forEach(row => {
            html += '<tr>';
            cabecera.forEach(col => {
                let valor = row[col] ?? '';

                if (col === 'Riesgo') {
                    let color = 'gray';
                    if (valor === 'Alto') color = '#e74c3c';
                    else if (valor === 'Medio') color = '#f1c40f';
                    else if (valor === 'Bajo') color = '#2ecc71';
                    valor = `<span style="background-color: ${color}; padding: 4px 8px; border-radius: 4px; color: white;">${valor || 'Sin riesgo'}</span>`;
                } else if (['Presion', 'Temperatura', 'Volumen', 'Volumen_Predicho', 'Residual'].includes(col)) {
                    // Redondear numéricos a 2 decimales
                    valor = isNaN(parseFloat(valor)) ? valor : parseFloat(valor).toFixed(2);
                }

                html += `<td>${valor}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        contenedor.innerHTML = html;

    } catch (error) {
        console.error('Error al cargar la tabla de registros:', error);
        document.getElementById('tabla-registros').innerHTML = '<p style="color:red;">Error al cargar la tabla.</p>';
    }
}

function obtenerParametros() {
    const cliente = document.getElementById('cliente').value;
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    const riesgoSelect = document.getElementById('riesgoFiltro');
    const riesgosSeleccionados = Array.from(riesgoSelect.selectedOptions).map(opt => opt.value);

    const params = new URLSearchParams();
    if (cliente && cliente !== 'todos') params.append('cliente', cliente);
    if (fechaInicio) params.append('inicio', fechaInicio);
    if (fechaFin) params.append('fin', fechaFin);
    if (riesgosSeleccionados.length > 0) params.append('riesgos', riesgosSeleccionados.join(','));

    return params.toString();
}



async function actualizarRangoFechas() {
    const cliente = document.getElementById('cliente').value;
    const url = `/rangos_fechas?cliente=${cliente}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();

        const inputInicio = document.getElementById('fechaInicio');
        const inputFin = document.getElementById('fechaFin');

        // Establecer los límites de fechas
        inputInicio.min = data.min_fecha;
        inputInicio.max = data.max_fecha;
        inputFin.min = data.min_fecha;
        inputFin.max = data.max_fecha;

        // Si no hay valor seleccionado, establecer últimos 30 días
        const fechasPredefinidas = !inputInicio.value && !inputFin.value;
        if (fechasPredefinidas) {
            const hoy = new Date(data.max_fecha);
            const hace30 = new Date(hoy);
            hace30.setDate(hoy.getDate() - 30);

            const formatoFecha = (fecha) => fecha.toISOString().split('T')[0];
            inputInicio.value = formatoFecha(hace30);
            inputFin.value = formatoFecha(hoy);
        }

        // ⚡ Forzar carga de datos si las fechas fueron autoasignadas
        if (fechasPredefinidas) {
            cargarKPIs();
            cargarGraficoConsumo();
            cargarGraficoRiesgoCliente();
            cargarHeatmapAnomalias();
            cargarTablaRegistros();
        }

    } catch (error) {
        console.error('Error al obtener rango de fechas:', error);
    }
}



document.getElementById('cliente').addEventListener('change', () => {
    const cliente = document.getElementById('cliente').value;
    actualizarRangoFechas();
    cargarKPIs(cliente);
    cargarGraficoConsumo(cliente);
});


document.getElementById('btnGenerarPDF').addEventListener('click', () => {
    // Agrega clase temporal
    document.body.classList.add('exportar');

    const contenido = document.getElementById('contenido-exportar');
    const opciones = {
        margin: 0.5,
        filename: 'monitoreo_clientes.pdf',
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' }
    };

    html2pdf().set(opciones).from(contenido).save().then(() => {
        // Quita clase después de generar PDF
        document.body.classList.remove('exportar');
    });
});
window.onload = async () => {
    // Inicializa flatpickr en los inputs de fecha
    flatpickr("#fechaInicio", {
        dateFormat: "Y-m-d",
        maxDate: "today",
        defaultDate: document.getElementById('fechaInicio').value || null,
        locale: {
            firstDayOfWeek: 1
        }
    });
    flatpickr("#fechaFin", {
        dateFormat: "Y-m-d",
        maxDate: "today",
        defaultDate: document.getElementById('fechaFin').value || null,
        locale: {
            firstDayOfWeek: 1
        }
    });

    // Espera a que se asignen las fechas correctamente
    await actualizarRangoFechas(); // Esta ya recarga los datos si asigna las fechas por defecto

    // Pero si las fechas ya estaban definidas por el usuario (no fueron autoasignadas), carga los datos aquí:
    const fechaInicio = document.getElementById('fechaInicio').value;
    const fechaFin = document.getElementById('fechaFin').value;
    if (fechaInicio && fechaFin) {
        cargarKPIs();
        cargarGraficoConsumo();
        cargarGraficoRiesgoCliente();
        cargarHeatmapAnomalias();
        cargarTablaRegistros();
    }

    // Añadir listeners a los filtros
    ['cliente', 'fechaInicio', 'fechaFin', 'riesgoFiltro'].forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            cargarKPIs();
            cargarGraficoConsumo();
            cargarGraficoRiesgoCliente();
            cargarHeatmapAnomalias();
            cargarTablaRegistros();
        });
    });

    // Redimensionar gráficos
    window.addEventListener('resize', () => {
        if (window.myChart) window.myChart.resize();
        if (window.chartRiesgo) window.chartRiesgo.resize();
        if (window.chartHeatmap) window.chartHeatmap.resize();
    });

    document.getElementById('btnLimpiarFiltros').addEventListener('click', () => {
        document.getElementById('cliente').value = 'todos';
        document.getElementById('fechaInicio').value = '';
        document.getElementById('fechaFin').value = '';
        document.getElementById('riesgoFiltro').value = 'todos';

        actualizarRangoFechas(); // Esta función volverá a cargar los datos si establece nuevas fechas
    });

    document.getElementById('btnGenerarPDF').addEventListener('click', () => {
        document.body.classList.add('exportar');
        const contenido = document.getElementById('contenido-exportar');
        const opciones = {
            margin: 0.5,
            filename: 'monitoreo_clientes.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' }
        };
        html2pdf().set(opciones).from(contenido).save().then(() => {
            document.body.classList.remove('exportar');
        });
    });
};

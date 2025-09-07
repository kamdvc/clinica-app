// ==================== MÓDULO DE REPORTES MÉDICOS ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🏥 Inicializando módulo de reportes médicos...');
    
    // Variables globales para los gráficos
    let charts = {};
    
    // Cargar todos los datos al iniciar
    cargarReportes();
    
    async function cargarReportes() {
        try {
            document.getElementById('loading').style.display = 'block';
            
            // Cargar estadísticas generales
            await cargarEstadisticasGenerales();
            
            // Cargar enfermedades comunes
            await cargarEnfermedadesComunes();
            
            // Cargar problemas por sistemas
            await cargarProblemasPorSistemas();
            
            document.getElementById('loading').style.display = 'none';
            console.log('✅ Reportes cargados exitosamente');
            
        } catch (error) {
            console.error('❌ Error cargando reportes:', error);
            document.getElementById('loading').innerHTML = 
                '<div class="alert alert-danger">Error cargando los reportes. Por favor, intente nuevamente.</div>';
        }
    }
    
    async function cargarEstadisticasGenerales() {
        console.log('📊 Cargando estadísticas generales...');
        try {
            const response = await fetch(`/api/reportes/estadisticas_generales?_t=${Date.now()}`);
            if (!response.ok) {
                throw new Error(`Error en la respuesta de la API: ${response.statusText}`);
            }
            const result = await response.json();

            if (result.success) {
                const data = result.data;
                
                // Actualizar cards de estadísticas
                document.getElementById('total-pacientes').textContent = data.total_pacientes;
                document.getElementById('total-consultas').textContent = data.total_consultas;
                
                // Calcular y mostrar edad promedio
                let totalPacientesEdad = 0;
                let sumaEdades = 0;
                Object.entries(data.edad_distribucion).forEach(([rango, cantidad]) => {
                    if (cantidad > 0) {
                        const edadMedia = calcularEdadMediaRango(rango);
                        sumaEdades += edadMedia * cantidad;
                        totalPacientesEdad += cantidad;
                    }
                });
                const edadPromedio = totalPacientesEdad > 0 ? Math.round(sumaEdades / totalPacientesEdad) : 0;
                document.getElementById('promedio-edad').textContent = edadPromedio;

                // Consultas del mes actual (provisto por backend en TZ Guatemala)
                const consultasMesActual = data.consultas_mes_actual ?? (Object.values(data.consultas_por_mes).slice(-1)[0] || 0);
                document.getElementById('consultas-mes').textContent = consultasMesActual;

                // Crear gráficos
                crearGraficoGenero(data.genero_distribucion);
                crearGraficoEdad(data.edad_distribucion);
                crearGraficoConsultasMes(data.consultas_por_mes);
            } else {
                throw new Error(result.error || 'La API de estadísticas devolvió un error.');
            }
        } catch (error) {
            console.error('❌ Error fatal al cargar estadísticas generales:', error);
            document.getElementById('estadisticas-cards').innerHTML = 
                '<div class="col-12"><div class="alert alert-danger">No se pudieron cargar las estadísticas.</div></div>';
        }
    }
    
    function calcularEdadMediaRango(rango) {
        if (rango === '90+') return 95;
        const [min, max] = rango.split('-').map(Number);
        return (min + max) / 2;
    }
    
    function crearGraficoGenero(data) {
        const ctx = document.getElementById('generoChart').getContext('2d');
        
        const labels = Object.keys(data);
        const valores = Object.values(data);
        const total = valores.reduce((a, b) => a + b, 0);
        
        charts.genero = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels.map(label => {
                    const porcentaje = total > 0 ? Math.round((data[label] / total) * 100) : 0;
                    return `${label} (${porcentaje}%)`;
                }),
                datasets: [{
                    data: valores,
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#dc3545',
                        '#ffc107'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `Total: ${total} pacientes`,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            }
        });
    }
    
    function crearGraficoEdad(data) {
        const ctx = document.getElementById('edadChart').getContext('2d');
        
        // Filtrar rangos con datos > 0
        const labels = [];
        const valores = [];
        Object.entries(data).forEach(([rango, cantidad]) => {
            if (cantidad > 0) {
                labels.push(rango);
                valores.push(cantidad);
            }
        });
        
        charts.edad = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Número de Pacientes',
                    data: valores,
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Distribución por Rangos de Edad',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }
    
    function crearGraficoConsultasMes(data) {
        const ctx = document.getElementById('consultasMesChart').getContext('2d');
        
        const labels = Object.keys(data);
        const valores = Object.values(data);
        
        charts.consultasMes = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Consultas',
                    data: valores,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#007bff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    async function cargarEnfermedadesComunes() {
        console.log('🦠 Cargando enfermedades comunes...');
        
        const response = await fetch(`/api/reportes/enfermedades_comunes?_t=${Date.now()}`);
        const result = await response.json();
        
        if (result.success) {
            crearGraficoEnfermedades(result.data);
        }
    }
    
    function crearGraficoEnfermedades(data) {
        const ctx = document.getElementById('enfermedadesChart').getContext('2d');
        
        const labels = Object.keys(data);
        const valores = Object.values(data);
        
        charts.enfermedades = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Frecuencia',
                    data: valores,
                    backgroundColor: '#17a2b8',
                    borderColor: '#117a8b',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }
    
    async function cargarProblemasPorSistemas() {
        console.log('🏥 Cargando problemas por sistemas...');
        
        const response = await fetch(`/api/reportes/problemas_por_sistemas?_t=${Date.now()}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data || {};
            const hasData = Object.keys(data).length > 0;
            if (hasData) {
                crearGraficoSistemas(data);
            } else {
                mostrarMensajeSinDatosSistemas();
            }
        } else {
            mostrarMensajeSinDatosSistemas('No se pudieron cargar los datos del reporte por sistemas.');
        }
    }
    
    function crearGraficoSistemas(data) {
        const ctx = document.getElementById('sistemasChart').getContext('2d');
        
        const labels = Object.keys(data);
        const valores = Object.values(data);
        if (labels.length === 0) {
            mostrarMensajeSinDatosSistemas();
            return;
        }
        
        // Colores para cada sistema
        const colores = [
            '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
            '#6f42c1', '#e83e8c', '#fd7e14', '#20c997', '#6c757d',
            '#343a40', '#f8f9fa'
        ];
        
        charts.sistemas = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Casos',
                    data: valores,
                    backgroundColor: colores.slice(0, labels.length),
                    borderColor: colores.slice(0, labels.length).map(color => color + 'aa'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const sistema = labels[index];
                        mostrarDetalleSistema(sistema);
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                return 'Haga clic para ver detalles';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45
                        }
                    }
                }
            }
        });
    }

    function mostrarMensajeSinDatosSistemas(mensajePersonalizado) {
        const canvas = document.getElementById('sistemasChart');
        if (!canvas) return;
        const contenedor = canvas.parentElement;
        // Ocultar el canvas para evitar un espacio vacío
        canvas.style.display = 'none';
        const aviso = document.createElement('div');
        aviso.className = 'alert alert-info mb-0';
        aviso.textContent = mensajePersonalizado || 'No hay datos suficientes para mostrar "Problemas por Sistemas Médicos". Registre diagnósticos o motivos de consulta con palabras clave para este análisis.';
        contenedor.appendChild(aviso);
    }
    
    async function mostrarDetalleSistema(sistema) {
        console.log(`🔍 Mostrando detalle del sistema: ${sistema}`);
        
        try {
            const response = await fetch(`/api/reportes/sistema_detalle/${encodeURIComponent(sistema)}`);
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('sistemaModalTitle').textContent = `Sistema ${result.sistema}`;
                crearGraficoDetalleSistema(result.data, result.sistema);
                
                const modal = new bootstrap.Modal(document.getElementById('sistemaDetalleModal'));
                modal.show();
            }
        } catch (error) {
            console.error('Error cargando detalle del sistema:', error);
        }
    }
    
    function crearGraficoDetalleSistema(data, sistema) {
        const ctx = document.getElementById('sistemaDetalleChart').getContext('2d');
        
        // Destruir gráfico anterior si existe
        if (charts.sistemaDetalle) {
            charts.sistemaDetalle.destroy();
        }
        
        const labels = Object.keys(data);
        const valores = Object.values(data);
        
        charts.sistemaDetalle = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Casos',
                    data: valores,
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: `Desglose del Sistema ${sistema}`,
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    });
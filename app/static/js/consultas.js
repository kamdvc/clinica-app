// Logica para consultas.html

// Variables globales para manejo de formularios
let consultaActual = null;
let autoSaveEnabled = false;
let currentTab = 'datos-generales';
let revisionSistemasData = {};
let sistemaSeleccionado = null;


document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 DOM Content Loaded - Inicializando consultas.js');
    
    // Inicializar sistema de pestañas y autoguardado
    initTabSystem();
    initAutoSave();
    initRevisionSistemas();
    
    // Elementos de búsqueda actualizados
    const patientSearchInput = document.getElementById('patient-search');
    const searchPatientButton = document.getElementById('search-btn');
    const searchResultsDiv = document.getElementById('search-results');

    // Vital Signs Panel Elements
    const patientNameElement = document.getElementById('patient-name');
    const patientAgeElement = document.getElementById('patient-age');
    const patientGenderElement = document.getElementById('patient-gender');
    const vitalPresionArterialElement = document.getElementById('vital-presion-arterial');
    const vitalSaturacionElement = document.getElementById('vital-saturacion');
    const vitalTemperaturaElement = document.getElementById('vital-temperatura');
    const vitalFrecuenciaRespiratoriaElement = document.getElementById('vital-frecuencia-respiratoria');
    const vitalFrecuenciaCardiacaElement = document.getElementById('vital-frecuencia-cardiaca');
    const vitalGlucosaElement = document.getElementById('vital-glucosa');
    
    // Verificación de elementos críticos
    if (!patientSearchInput || !searchResultsDiv) {
        console.error('❌ Elementos de búsqueda no encontrados');
    } else {
        console.log('✅ Sistema de búsqueda de pacientes inicializado correctamente');
    }

    // Function to clear patient information in the vital signs panel
    function clearPatientInfo() {
        if (patientNameElement) patientNameElement.textContent = 'Seleccione un paciente';
        if (patientAgeElement) patientAgeElement.textContent = '-- AÑOS';
        if (patientGenderElement) patientGenderElement.textContent = '--';
        if (vitalPresionArterialElement) vitalPresionArterialElement.textContent = '--';
        if (vitalSaturacionElement) vitalSaturacionElement.textContent = '--%';
        if (vitalTemperaturaElement) vitalTemperaturaElement.textContent = '--';
        if (vitalFrecuenciaRespiratoriaElement) vitalFrecuenciaRespiratoriaElement.textContent = '-- rpm';
        if (vitalFrecuenciaCardiacaElement) vitalFrecuenciaCardiacaElement.textContent = '-- rpm';
        if (vitalGlucosaElement) vitalGlucosaElement.textContent = '-- mg/dl';
        
        // Limpiar historial médico
        clearMedicalHistory();
    }
    
    // Function to clear medical history
    function clearMedicalHistory() {
        const historialTotalEl = document.getElementById('historial-total');
        const historialContainer = document.getElementById('historial-container');
        const btnDescargarPDF = document.getElementById('btn-descargar-pdf');
        
        if (historialTotalEl) {
            historialTotalEl.textContent = 'No hay consultas previas';
        }
        
        if (historialContainer) {
            historialContainer.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-clipboard-list fa-2x mb-2"></i>
                    <p>Seleccione un paciente para ver su historial médico</p>
                </div>
            `;
        }
        
        // Ocultar botón PDF
        if (btnDescargarPDF) {
            btnDescargarPDF.style.display = 'none';
        }
        
        // Ocultar controles del formulario
        hideFormControls();
        
        // Limpiar paciente actual
        window.currentPatient = null;
    }

    // Function to update the vital signs panel with patient data (deprecated - usando selectPatient directamente)
    function updateVitalSignsPanel(patient) {
        // Esta función ahora está integrada en selectPatient para mayor robustez
        console.log('⚠️ updateVitalSignsPanel está deprecada - usar selectPatient directamente');
    }

    // Event listener for the search button
    if (searchPatientButton) {
        searchPatientButton.addEventListener('click', function () {
            performSearch();
        });
    }

    // Función para realizar la búsqueda
    async function performSearch() {
        const searchTerm = patientSearchInput.value.trim();
        if (!searchTerm) {
            searchResultsDiv.innerHTML = '';
            searchResultsDiv.classList.remove('show');
            return;
        }

        if (searchTerm.length < 2) {
            return;
        }

        try {
            const response = await fetch(`/api/buscar_pacientes?q=${encodeURIComponent(searchTerm)}`);
            if (!response.ok) {
                throw new Error('Error en la búsqueda');
            }
            const patients = await response.json();
            displaySearchResults(patients);
        } catch (error) {
            console.error('Error fetching search results:', error);
            searchResultsDiv.innerHTML = '<div class="dropdown-item text-danger">Error al buscar pacientes</div>';
            searchResultsDiv.classList.add('show');
        }
    }

    // Function to display search results in dropdown
    function displaySearchResults(patients) {
        searchResultsDiv.innerHTML = '';
        if (patients.length > 0) {
            patients.forEach(patient => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'dropdown-item d-flex justify-content-between align-items-center';
                item.innerHTML = `
                    <div>
                        <strong>${patient.nombre_completo}</strong><br>
                        <small class="text-muted">DPI: ${patient.dni || 'No registrado'} | Edad: ${patient.edad} años</small>
                    </div>
                    <i class="fas fa-user-check text-primary"></i>
                `;
                item.addEventListener('click', () => {
                    console.log('🖱️ Clic detectado en paciente:', patient.nombre_completo);
                    selectPatient(patient);
                });
                searchResultsDiv.appendChild(item);
            });
            searchResultsDiv.classList.add('show');
        } else {
            searchResultsDiv.innerHTML = '<div class="dropdown-item text-muted">No se encontraron pacientes</div>';
            searchResultsDiv.classList.add('show');
        }
    }

    // Function to select a patient and update panel
    function selectPatient(patient) {
        console.log('🎯 selectPatient - Paciente seleccionado:', patient);
        // Depuración: mostrar historial de consultas
        if (patient.historial_consultas && patient.historial_consultas.length > 0) {
            console.log('Primer objeto del historial:', patient.historial_consultas[0]);
            if (!patient.historial_consultas[0].id) {
                alert('El primer objeto del historial no tiene campo id.\n' + JSON.stringify(patient.historial_consultas[0]));
            }
        } else {
            console.log('El paciente no tiene historial de consultas.');
        }
        // Limpiar datos del paciente anterior
        clearPreviousPatientData();
        // Guardar paciente actual para acceso global
        window.currentPatient = patient;
        // Método directo y robusto para actualizar el panel
        try {
            // Actualizar nombre del paciente
            const nameEl = document.getElementById('patient-name');
            if (nameEl) {
                nameEl.textContent = patient.nombre_completo || 'N/A';
                console.log('✅ Nombre actualizado:', patient.nombre_completo);
            } else {
                console.error('❌ No se encontró elemento patient-name');
            }
            // Actualizar edad
            const ageEl = document.getElementById('patient-age');
            if (ageEl) {
                ageEl.textContent = patient.edad ? `${patient.edad} AÑOS` : '-- AÑOS';
                console.log('✅ Edad actualizada:', patient.edad);
            } else {
                console.error('❌ No se encontró elemento patient-age');
            }
            // Actualizar género
            const genderEl = document.getElementById('patient-gender');
            if (genderEl) {
                genderEl.textContent = patient.genero || '--';
                console.log('✅ Género actualizado:', patient.genero);
            } else {
                console.error('❌ No se encontró elemento patient-gender');
            }
            // Actualizar signos vitales si existen
            if (patient.signos_vitales) {
                console.log('🔍 Actualizando signos vitales:', patient.signos_vitales);
                const updateVitalElement = (id, value, suffix = '') => {
                    const el = document.getElementById(id);
                    if (el) {
                        el.textContent = value ? `${value}${suffix}` : '--';
                    } else {
                        console.error(`❌ No se encontró elemento ${id}`);
                    }
                };
                updateVitalElement('vital-presion-arterial', patient.signos_vitales.presion_arterial);
                updateVitalElement('vital-saturacion', patient.signos_vitales.saturacion, '%');
                updateVitalElement('vital-temperatura', patient.signos_vitales.temperatura);
                updateVitalElement('vital-frecuencia-respiratoria', patient.signos_vitales.frecuencia_respiratoria, ' rpm');
                updateVitalElement('vital-frecuencia-cardiaca', patient.signos_vitales.frecuencia_cardiaca, ' rpm');
                updateVitalElement('vital-glucosa', patient.signos_vitales.glucosa, ' mg/dl');
            } else {
                console.log('⚠️ Sin signos vitales - limpiar panel');
                // Limpiar signos vitales
                const vitalIds = ['vital-presion-arterial', 'vital-saturacion', 'vital-temperatura', 'vital-frecuencia-respiratoria', 'vital-frecuencia-cardiaca', 'vital-glucosa'];
                vitalIds.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = '--';
                });
            }
            // Actualizar campos de datos generales
            updateGeneralDataFields(patient);
            // Actualizar información en la pestaña de receta
            updateRecetaPatientInfo(patient);
            // Actualizar la fecha en la receta a la fecha actual
            const hoy = new Date();
            const fechaFormateada = `${hoy.getDate().toString().padStart(2, '0')}/${(hoy.getMonth() + 1).toString().padStart(2, '0')}/${hoy.getFullYear()}`;
            document.getElementById('receta-fecha').textContent = fechaFormateada;
            // Actualizar historial médico
            updateMedicalHistory(patient);
            // Buscar la consulta más reciente del paciente
            findOrCreateConsultaForPatient(patient);
            // Forzar asignación de id si existe
            if (patient.historial_consultas && patient.historial_consultas.length > 0 && patient.historial_consultas[0].id) {
                consultaActual = patient.historial_consultas[0];
                consultaActual.id = patient.historial_consultas[0].id;
            }
            // Mostrar indicadores de autoguardado y botón limpiar
            showFormControls();
            // Restaurar datos guardados para este paciente después de un breve delay
            setTimeout(() => {
                restoreFormData();
            }, 300);
        } catch (error) {
            console.error('❌ Error en selectPatient:', error);
        }
        // Cerrar dropdown de resultados
        if (searchResultsDiv) {
            searchResultsDiv.classList.remove('show');
            searchResultsDiv.innerHTML = '';
        }
        // Establecer el nombre del paciente en el campo de búsqueda
        if (patientSearchInput) {
            patientSearchInput.value = patient.nombre_completo;
            console.log('✅ Campo de búsqueda actualizado');
        }
        console.log('✅ Proceso de selección completado');
    }

    // Función para actualizar los campos de datos generales
    function updateGeneralDataFields(patient) {
        console.log('📝 updateGeneralDataFields - Datos del paciente:', patient);
        
        // Buscar y actualizar campos de datos generales en las pestañas
        const fields = {
            'estado_civil': patient.estado_civil,
            'dni': patient.dni,
            'religion': patient.religion,
            'escolaridad': patient.escolaridad,
            'ocupacion': patient.ocupacion,
            'direccion': patient.direccion,
            'procedencia': patient.procedencia,
            'telefono': patient.telefono,
            'numero_expediente': patient.numero_expediente
        };

        console.log('📝 Campos a actualizar:', fields);

        // Actualizar campos por name attribute
        let fieldsUpdated = 0;
        Object.keys(fields).forEach(fieldName => {
            const field = document.querySelector(`input[name="${fieldName}"], textarea[name="${fieldName}"]`);
            if (field && fields[fieldName]) {
                field.value = fields[fieldName];
                fieldsUpdated++;
            } else if (!field) {
                console.log(`⚠️ Campo no encontrado: ${fieldName}`);
            }
        });

        // También intentar por ID si no se encuentran por name
        Object.keys(fields).forEach(fieldName => {
            const field = document.getElementById(fieldName);
            if (field && fields[fieldName]) {
                field.value = fields[fieldName];
                fieldsUpdated++;
            }
        });
        
        console.log(`📊 Campos de datos generales actualizados: ${fieldsUpdated}`);
        
        // Controlar visibilidad de sección de antecedentes según género
        toggleAntecedentesSection(patient.genero === 'Femenino');
    }

    /**
     * Controla la visibilidad de la sección de antecedentes según el género del paciente
     */
    function toggleAntecedentesSection(showForFemale) {
        console.log(`👩‍⚕️ Controlando visibilidad de antecedentes: ${showForFemale ? 'mostrar (femenino)' : 'ocultar (masculino)'}`);
        
        const antecedentesSection = document.getElementById('antecedentes-section');
        if (antecedentesSection) {
            antecedentesSection.style.display = showForFemale ? 'block' : 'none';
            console.log(`✅ Sección de antecedentes ${showForFemale ? 'mostrada' : 'ocultada'}`);
        } else {
            console.error('❌ No se encontró el elemento antecedentes-section');
        }
    }

    // Función para actualizar el historial médico
    function updateMedicalHistory(patient) {
        console.log('📋 Actualizando historial médico...');
        
        const historialTotalEl = document.getElementById('historial-total');
        const historialContainer = document.getElementById('historial-container');
        
        if (!historialContainer) {
            console.error('❌ No se encontró el contenedor del historial');
            return;
        }
        
        const historial = patient.historial_consultas || [];
        
        // Actualizar contador y mostrar/ocultar botón PDF
        const btnDescargarPDF = document.getElementById('btn-descargar-pdf');
        if (historialTotalEl) {
            historialTotalEl.textContent = historial.length > 0 ? 
                `${historial.length} consulta${historial.length > 1 ? 's' : ''} previa${historial.length > 1 ? 's' : ''}` : 
                'No hay consultas previas';
        }
        
        // Mostrar botón PDF solo si hay historial
        if (btnDescargarPDF) {
            if (historial.length > 0) {
                btnDescargarPDF.style.display = 'block';
            } else {
                btnDescargarPDF.style.display = 'none';
            }
        }
        
        if (historial.length === 0) {
            historialContainer.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-clipboard-list fa-2x mb-2"></i>
                    <p>No hay historial médico disponible para este paciente</p>
                </div>
            `;
            return;
        }
        
        // Generar HTML del historial
        let historialHTML = '';
        historial.forEach((consulta, index) => {
            const isFirst = index === 0;
            historialHTML += `
                <div class="border-bottom p-3 ${isFirst ? 'bg-light' : ''}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0 text-primary">
                            <i class="fas fa-stethoscope me-1"></i>
                            ${consulta.tipo_consulta}
                            ${isFirst ? '<span class="badge bg-primary ms-2">Más reciente</span>' : ''}
                        </h6>
                        <small class="text-muted">${consulta.fecha}</small>
                    </div>
                    
                    ${consulta.medico ? `<p class="mb-2 small"><strong>Médico:</strong> ${consulta.medico}</p>` : ''}
                    
                    ${consulta.motivo_consulta ? `
                        <div class="mb-2">
                            <strong class="small text-success">Motivo de consulta:</strong>
                            <p class="small mb-0">${consulta.motivo_consulta}</p>
                        </div>
                    ` : ''}
                    
                    ${consulta.diagnostico ? `
                        <div class="mb-2">
                            <strong class="small text-danger">Diagnóstico:</strong>
                            <p class="small mb-0">${consulta.diagnostico}</p>
                        </div>
                    ` : ''}
                    
                    ${consulta.tratamiento ? `
                        <div class="mb-2">
                            <strong class="small text-info">Tratamiento:</strong>
                            <p class="small mb-0">${consulta.tratamiento}</p>
                        </div>
                    ` : ''}
                    
                    ${consulta.historia_enfermedad ? `
                        <div class="mb-2">
                            <strong class="small text-warning">Historia de la enfermedad:</strong>
                            <p class="small mb-0">${consulta.historia_enfermedad}</p>
                        </div>
                    ` : ''}
                    
                    <!-- Signos vitales de esta consulta -->
                    ${consulta.signos_vitales || consulta.presion_arterial ? `
                        <div class="mt-2 pt-2 border-top">
                            <strong class="small text-secondary">Signos vitales:</strong>
                            <div class="row g-1 mt-1">
                                ${consulta.signos_vitales?.presion_arterial || consulta.presion_arterial ? 
                                    `<div class="col-4"><small>P/A: ${consulta.signos_vitales?.presion_arterial || consulta.presion_arterial}</small></div>` : ''}
                                ${consulta.signos_vitales?.temperatura || consulta.temperatura ? 
                                    `<div class="col-4"><small>T°: ${consulta.signos_vitales?.temperatura || consulta.temperatura}</small></div>` : ''}
                                ${consulta.signos_vitales?.frecuencia_cardiaca || consulta.frecuencia_cardiaca ? 
                                    `<div class="col-4"><small>FC: ${consulta.signos_vitales?.frecuencia_cardiaca || consulta.frecuencia_cardiaca}</small></div>` : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Botón para ver detalles completos + PDF -->
                    <div class="mt-2 d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="showConsultaDetails(${consulta.id}, '${consulta.fecha}')">
                            <i class="fas fa-eye me-1"></i> Ver detalles completos
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="descargarConsultaPDF(${consulta.id})">
                            <i class="fas fa-file-pdf me-1"></i> PDF de esta consulta
                        </button>
                    </div>
                </div>
            `;
        });
        
        historialContainer.innerHTML = historialHTML;
        console.log(`✅ Historial médico actualizado con ${historial.length} consulta(s)`);
    }

    // Función global para mostrar detalles completos de una consulta
    window.showConsultaDetails = function(consultaId, fecha) {
        console.log(`🔍 Mostrando detalles de consulta ID: ${consultaId}`);
        
        // Buscar la consulta en el historial del paciente actual
        if (!window.currentPatient || !window.currentPatient.historial_consultas) {
            console.error('❌ No hay paciente seleccionado o sin historial');
            return;
        }
        
        const consulta = window.currentPatient.historial_consultas.find(c => c.id === consultaId);
        if (!consulta) {
            console.error('❌ Consulta no encontrada');
            return;
        }
        
        // Crear modal con detalles completos
        const modalHTML = `
            <div class="modal fade" id="consultaDetailsModal" tabindex="-1" aria-labelledby="consultaDetailsModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="consultaDetailsModalLabel">
                                <i class="fas fa-file-medical me-2"></i>
                                Detalles de Consulta - ${fecha}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-primary border-bottom pb-2">Información General</h6>
                                    <p><strong>Tipo de consulta:</strong> ${consulta.tipo_consulta}</p>
                                    <p><strong>Médico:</strong> ${consulta.medico}</p>
                                    <p><strong>Fecha:</strong> ${fecha}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6 class="text-primary border-bottom pb-2">Signos Vitales</h6>
                                    ${consulta.signos_vitales ? `
                                        <div class="row g-2">
                                            <div class="col-6"><small><strong>P/A:</strong> ${consulta.signos_vitales.presion_arterial || '--'}</small></div>
                                            <div class="col-6"><small><strong>T°:</strong> ${consulta.signos_vitales.temperatura || '--'}</small></div>
                                            <div class="col-6"><small><strong>FC:</strong> ${consulta.signos_vitales.frecuencia_cardiaca || '--'}</small></div>
                                            <div class="col-6"><small><strong>FR:</strong> ${consulta.signos_vitales.frecuencia_respiratoria || '--'}</small></div>
                                            <div class="col-6"><small><strong>SatO2:</strong> ${consulta.signos_vitales.saturacion || '--'}%</small></div>
                                            <div class="col-6"><small><strong>Glucosa:</strong> ${consulta.signos_vitales.glucosa || '--'}</small></div>
                                        </div>
                                    ` : '<p class="text-muted">No registrados</p>'}
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <h6 class="text-success border-bottom pb-2">Motivo de Consulta</h6>
                                <p>${consulta.motivo_consulta || 'No registrado'}</p>
                            </div>
                            
                            <div class="mt-3">
                                <h6 class="text-warning border-bottom pb-2">Historia de la Enfermedad</h6>
                                <p>${consulta.historia_enfermedad || 'No registrada'}</p>
                            </div>
                            
                            <div class="mt-3">
                                <h6 class="text-info border-bottom pb-2">Revisión por Sistemas</h6>
                                <p>${consulta.revision_sistemas || 'No registrada'}</p>
                            </div>
                            
                            <div class="mt-3">
                                <h6 class="text-secondary border-bottom pb-2">Antecedentes</h6>
                                <p>${consulta.antecedentes || 'No registrados'}</p>
                            </div>
                            
                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <h6 class="text-danger border-bottom pb-2">Diagnóstico</h6>
                                    <p>${consulta.diagnostico || 'No registrado'}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6 class="text-primary border-bottom pb-2">Tratamiento</h6>
                                    <p>${consulta.tratamiento || 'No registrado'}</p>
                                </div>
                            </div>
                            
                                        ${(consulta.gestas || consulta.partos || consulta.abortos) && window.currentPatient && window.currentPatient.genero === 'Femenino' ? `
                <div class="mt-3">
                    <h6 class="text-purple border-bottom pb-2">Antecedentes Gineco-Obstétricos</h6>
                    <div class="row">
                        <div class="col-3"><small><strong>Gestas:</strong> ${consulta.gestas || '--'}</small></div>
                        <div class="col-3"><small><strong>Partos:</strong> ${consulta.partos || '--'}</small></div>
                        <div class="col-3"><small><strong>Abortos:</strong> ${consulta.abortos || '--'}</small></div>
                        <div class="col-3"><small><strong>H. vivos:</strong> ${consulta.hijos_vivos || '--'}</small></div>
                    </div>
                    ${consulta.fecha_ultima_regla ? `<p><strong>Fecha última regla:</strong> ${consulta.fecha_ultima_regla}</p>` : ''}
                </div>
            ` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <button type="button" class="btn btn-primary" onclick="descargarConsultaPDF(${consultaId})">
                                <i class="fas fa-file-pdf me-1"></i> PDF de esta consulta
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remover modal previo si existe
        const existingModal = document.getElementById('consultaDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Agregar modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('consultaDetailsModal'));
        modal.show();
    }

    // Autocomplete functionality en tiempo real
    if (patientSearchInput) {
        let searchTimeout;
        
        patientSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const term = this.value.trim();
            
            if (term.length < 2) {
                searchResultsDiv.innerHTML = '';
                searchResultsDiv.classList.remove('show');
                return;
            }

            // Debounce de 300ms para evitar demasiadas consultas
            searchTimeout = setTimeout(() => {
                performSearchAutocomplete(term);
            }, 300);
        });

        // Manejar Enter para buscar
        patientSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch();
            }
        });

        // Ocultar resultados al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.input-group') && !searchResultsDiv.contains(e.target)) {
                searchResultsDiv.classList.remove('show');
            }
        });
    }

    // Función para autocompletado más rápido
    async function performSearchAutocomplete(term) {
        try {
            const response = await fetch(`/api/buscar_pacientes?q=${encodeURIComponent(term)}`);
            if (!response.ok) {
                return;
            }
            const patients = await response.json();
            displaySearchResults(patients);
        } catch (error) {
            console.error('Error en autocompletado:', error);
        }
    }

    // Initial clear of patient info when the page loads
    clearPatientInfo();
    
    // Función de prueba para debugging - disponible globalmente
    window.testPatientSelection = function() {
        console.log('🧪 Ejecutando prueba de selección de paciente...');
        const testPatient = {
            nombre_completo: 'Paciente de Prueba',
            edad: 35,
            genero: 'Masculino',
            dni: '12345678',
            telefono: '555-1234',
            direccion: 'Calle Falsa 123',
            estado_civil: 'Soltero',
            religion: 'Católica',
            escolaridad: 'Universitaria',
            ocupacion: 'Ingeniero',
            procedencia: 'San Salvador',
            numero_expediente: 'EXP-001',
            signos_vitales: {
                presion_arterial: '120/80',
                saturacion: '98',
                temperatura: '36.5',
                frecuencia_respiratoria: '18',
                frecuencia_cardiaca: '72',
                glucosa: '95'
            },
            historial_consultas: [
                {
                    id: 1,
                    fecha: '15/12/2024 10:30',
                    tipo_consulta: 'Primera consulta',
                    medico: 'Dr. Juan Pérez',
                    motivo_consulta: 'Dolor de cabeza persistente',
                    historia_enfermedad: 'Paciente refiere cefalea frontal de 3 días de evolución',
                    diagnostico: 'Cefalea tensional',
                    tratamiento: 'Paracetamol 500mg cada 8 horas',
                    signos_vitales: {
                        presion_arterial: '118/75',
                        temperatura: '36.3',
                        frecuencia_cardiaca: '70'
                    }
                },
                {
                    id: 2,
                    fecha: '10/12/2024 14:15',
                    tipo_consulta: 'Seguimiento',
                    medico: 'Dr. María González',
                    motivo_consulta: 'Control de presión arterial',
                    historia_enfermedad: 'Paciente en tratamiento antihipertensivo',
                    diagnostico: 'Hipertensión arterial controlada',
                    tratamiento: 'Continuar con Enalapril 10mg/día',
                    signos_vitales: {
                        presion_arterial: '130/85',
                        temperatura: '36.4',
                        frecuencia_cardiaca: '75'
                    }
                }
            ],
            total_consultas: 2
        };
        
        selectPatient(testPatient);
        console.log('✅ Prueba completada - verifica el panel lateral e historial médico');
    };
    
    console.log('💡 Para probar manualmente, ejecuta: testPatientSelection()');
    
    // Configurar navegación entre pestañas desde el inicio
    setupTabNavigation();
});

// ==================== SISTEMA DE AUTOGUARDADO ====================

function initAutoSaveForPatient() {
    console.log('💾 Inicializando autoguardado para paciente:', window.currentPatient?.nombre_completo);
    
    // Limpiar listeners anteriores para evitar duplicados
    cleanupAutoSaveListeners();
    
    // Configurar autoguardado para todos los campos de formulario
    setupFormAutoSave();
    
    console.log('✅ Autoguardado configurado para el paciente actual');
}

function cleanupAutoSaveListeners() {
    // Esta función se mantendrá simple por ahora
    // Los nuevos listeners se configurarán cuando sea necesario
    console.log('🧹 Limpiando listeners anteriores...');
}

function setupFormAutoSave() {
    // Detectar todos los campos de formulario
    const formFields = document.querySelectorAll('input, textarea, select');
    console.log(`🔍 Configurando autoguardado para ${formFields.length} campos...`);
    
    formFields.forEach((field, index) => {
        const fieldInfo = `${field.name || field.id || 'sin-nombre'} (${field.type || field.tagName})`;
        
        // Función de guardado con debugging
        const saveWithDebug = () => {
            console.log(`💾 Cambio detectado en: ${fieldInfo}`);
            saveFormData();
        };
        
        // Agregar listeners para diferentes tipos de eventos
        field.addEventListener('input', saveWithDebug);
        field.addEventListener('change', saveWithDebug);
        field.addEventListener('blur', saveWithDebug);
        
        // Log de cada campo configurado
        if (index < 5) { // Solo mostrar los primeros 5 para no saturar la consola
            console.log(`🔗 Campo ${index + 1}: ${fieldInfo}`);
        }
    });
    
    console.log(`✅ Autoguardado configurado para ${formFields.length} campos`);
}

function saveFormData() {
    if (!window.currentPatient) {
        console.log('⚠️ No hay paciente seleccionado para guardar datos');
        return; // No guardar si no hay paciente seleccionado
    }
    
    console.log('💾 Iniciando guardado de datos para:', window.currentPatient.nombre_completo);
    const formData = {};
    let fieldsProcessed = 0;
    
    // Recopilar datos de todos los formularios
    const allFields = document.querySelectorAll('input, textarea, select');
    console.log(`🔍 Encontrados ${allFields.length} campos en total`);
    
    allFields.forEach(field => {
        if (field.name || field.id) {
            const key = field.name || field.id;
            
            // Excluir campos del panel de búsqueda
            if (key === 'patient-search') {
                return;
            }
            
            // Manejar diferentes tipos de campos
            if (field.type === 'checkbox') {
                formData[key] = field.checked;
            } else if (field.type === 'radio') {
                if (field.checked) {
                    formData[key] = field.value;
                }
            } else {
                formData[key] = field.value;
            }
            
            fieldsProcessed++;
        }
    });
    
    console.log(`📊 Procesados ${fieldsProcessed} campos con datos`);
    
    // Guardar en localStorage con el ID del paciente
    const storageKey = `consulta_${window.currentPatient.id}`;
    localStorage.setItem(storageKey, JSON.stringify(formData));
    
    // Mostrar indicador de autoguardado
    showAutosaveIndicator();
    
    console.log('✅ Datos guardados exitosamente:', Object.keys(formData).length, 'campos');
    console.log('📝 Datos guardados:', formData);
}

function showAutosaveIndicator() {
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.style.display = 'block';
        indicator.innerHTML = '<i class="fas fa-check-circle me-1 text-success"></i>Guardado';
        
        // Volver al estado normal después de 2 segundos
        setTimeout(() => {
            indicator.innerHTML = '<i class="fas fa-save me-1"></i>Autoguardado activado';
        }, 2000);
    }
}

function restoreFormData() {
    if (!window.currentPatient) {
        console.log('⚠️ No hay paciente seleccionado para restaurar datos');
        return;
    }
    
    const storageKey = `consulta_${window.currentPatient.id}`;
    const savedData = localStorage.getItem(storageKey);
    
    if (!savedData) {
        console.log('ℹ️ No hay datos guardados para este paciente');
        return;
    }
    
    try {
        const formData = JSON.parse(savedData);
        console.log('🔄 Restaurando datos para:', window.currentPatient.nombre_completo);
        console.log('📂 Datos a restaurar:', formData);
        
        let fieldsRestored = 0;
        let fieldsNotFound = 0;
        
        // Restaurar valores en los campos
        Object.keys(formData).forEach(key => {
            const field = document.querySelector(`[name="${key}"], #${key}`);
            
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = formData[key];
                } else if (field.type === 'radio') {
                    if (field.value === formData[key]) {
                        field.checked = true;
                    }
                } else {
                    field.value = formData[key];
                }
                fieldsRestored++;
                console.log(`✅ Campo restaurado: ${key} = ${formData[key]}`);
            } else {
                fieldsNotFound++;
                console.warn(`⚠️ Campo no encontrado: ${key}`);
            }
        });
        
        console.log(`📊 Restauración completada: ${fieldsRestored} campos restaurados, ${fieldsNotFound} no encontrados`);
        
    } catch (error) {
        console.error('❌ Error al restaurar datos:', error);
    }
}

function clearFormData() {
    if (!window.currentPatient) {
        return;
    }
    
    const storageKey = `consulta_${window.currentPatient.id}`;
    localStorage.removeItem(storageKey);
    
    // Limpiar todos los campos del formulario
    const allFields = document.querySelectorAll('input, textarea, select');
    allFields.forEach(field => {
        if (!field.name || !['estado_civil', 'religion', 'escolaridad', 'ocupacion', 'direccion', 'procedencia', 'telefono', 'numero_expediente'].includes(field.name)) {
            if (field.type === 'checkbox' || field.type === 'radio') {
                field.checked = false;
            } else {
                field.value = '';
            }
        }
    });
    
    console.log('🗑️ Datos del formulario limpiados');
}

function setupTabNavigation() {
    console.log('🔄 Configurando navegación entre pestañas...');
    
    // Detectar clicks en las pestañas
    const tabButtons = document.querySelectorAll('.nav-link[data-bs-toggle="tab"]');
    console.log(`📋 Encontradas ${tabButtons.length} pestañas`);
    
    tabButtons.forEach((tab, index) => {
        console.log(`🔗 Configurando pestaña ${index + 1}: ${tab.textContent.trim()}`);
        
        // Evento ANTES de cambiar de pestaña (guardar datos actuales)
        tab.addEventListener('click', function(e) {
            console.log(`🔄 Cambiando a pestaña: ${this.textContent.trim()}`);
            
            // Guardar datos de la pestaña actual
            if (window.currentPatient) {
                console.log('💾 Guardando datos antes del cambio de pestaña...');
                saveFormData();
            }
        });
        
        // Evento DESPUÉS de cambiar de pestaña (restaurar datos)
        tab.addEventListener('shown.bs.tab', function(e) {
            console.log(`✅ Pestaña mostrada: ${this.textContent.trim()}`);
            
            // Restaurar datos en la nueva pestaña
            if (window.currentPatient) {
                console.log('🔄 Restaurando datos en la nueva pestaña...');
                setTimeout(() => {
                    restoreFormData();
                }, 50);
            }
        });
    });
    
    console.log('✅ Navegación entre pestañas configurada');
}

// Función para limpiar datos cuando se selecciona un nuevo paciente
function clearPreviousPatientData() {
    // Limpiar datos del paciente anterior si existe
    if (window.currentPatient) {
        saveFormData(); // Guardar datos actuales antes de cambiar
    }
    
    // Los datos se mantendrán en localStorage para cada paciente individualmente
    console.log('🔄 Preparando cambio de paciente');
}

function showFormControls() {
    // Mostrar indicador de autoguardado
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.style.display = 'block';
    }
    
    // Mostrar botón de debug
    const btnDebug = document.getElementById('btn-debug-autosave');
    if (btnDebug) {
        btnDebug.style.display = 'block';
    }
    
    // Mostrar botón de limpiar formulario
    const btnLimpiar = document.getElementById('btn-limpiar-formulario');
    if (btnLimpiar) {
        btnLimpiar.style.display = 'block';
    }
}

function hideFormControls() {
    // Ocultar indicador de autoguardado
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
    
    // Ocultar botón de debug
    const btnDebug = document.getElementById('btn-debug-autosave');
    if (btnDebug) {
        btnDebug.style.display = 'none';
    }
    
    // Ocultar botón de limpiar formulario
    const btnLimpiar = document.getElementById('btn-limpiar-formulario');
    if (btnLimpiar) {
        btnLimpiar.style.display = 'none';
    }
}

// Función global para limpiar el formulario
window.limpiarFormulario = function() {
    if (!window.currentPatient) {
        alert('No hay un paciente seleccionado.');
        return;
    }
    
    const confirmacion = confirm('¿Está seguro de que desea limpiar todos los datos del formulario? Esta acción no se puede deshacer.');
    
    if (confirmacion) {
        // Limpiar datos del localStorage
        const storageKey = `consulta_${window.currentPatient.id}`;
        localStorage.removeItem(storageKey);
        
        // Limpiar todos los campos del formulario excepto los de datos generales
        const allFields = document.querySelectorAll('input, textarea, select');
        allFields.forEach(field => {
            if (field.name && !['estado_civil', 'religion', 'escolaridad', 'ocupacion', 'direccion', 'procedencia', 'telefono', 'numero_expediente', 'patient-search'].includes(field.name)) {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    field.checked = false;
                } else {
                    field.value = '';
                }
            }
        });
        
        console.log('🗑️ Formulario limpiado para el paciente:', window.currentPatient.nombre_completo);
        alert('Formulario limpiado exitosamente.');
    }
};

// Función global para descargar PDF del historial médico
window.descargarHistorialPDF = function() {
    console.log('📄 Descargando PDF del historial médico...');
    
    if (!window.currentPatient) {
        console.error('❌ No hay paciente seleccionado');
        alert('Por favor, seleccione un paciente primero.');
        return;
    }
    
    if (!window.currentPatient.historial_consultas || window.currentPatient.historial_consultas.length === 0) {
        console.error('❌ No hay historial médico para descargar');
        alert('Este paciente no tiene historial médico para descargar.');
        return;
    }
    
    // Crear URL para descargar PDF
    const pdfUrl = `/descargar_historial_pdf/${window.currentPatient.id}`;
    console.log(`📥 Descargando PDF desde: ${pdfUrl}`);
    
    // Crear enlace temporal y hacer clic para descargar
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `historial_medico_${window.currentPatient.nombre_completo.replace(/\s+/g, '_')}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('✅ Descarga iniciada');
};

// ==================== FUNCIONES DE DEBUGGING ====================

// Función global para debuggear el autoguardado
window.debugAutoSave = function() {
    console.log('🐛 === DEBUG AUTOGUARDADO ===');
    console.log('👤 Paciente actual:', window.currentPatient);
    
    if (window.currentPatient) {
        const storageKey = `consulta_${window.currentPatient.id}`;
        const savedData = localStorage.getItem(storageKey);
        console.log('💾 Datos guardados:', savedData ? JSON.parse(savedData) : 'No hay datos');
        
        // Mostrar campos con valores
        const allFields = document.querySelectorAll('input, textarea, select');
        const fieldsWithValues = [];
        
        allFields.forEach(field => {
            if ((field.name || field.id) && field.value && field.value.trim() !== '') {
                fieldsWithValues.push({
                    name: field.name || field.id,
                    type: field.type || field.tagName,
                    value: field.value
                });
            }
        });
        
        console.log('📝 Campos con valores actuales:', fieldsWithValues);
        console.log('🔧 Para forzar guardado: forceAutoSave()');
        console.log('🔧 Para forzar restauración: forceRestore()');
    }
    console.log('🐛 === FIN DEBUG ===');
};

// Función para forzar guardado manual
window.forceAutoSave = function() {
    console.log('🔧 Forzando guardado manual...');
    saveFormData();
};

// Función para forzar restauración manual
window.forceRestore = function() {
    console.log('🔧 Forzando restauración manual...');
    restoreFormData();
};

console.log('🎯 Funciones de debugging disponibles:');
console.log('  - debugAutoSave() - Ver estado del autoguardado');
console.log('  - forceAutoSave() - Forzar guardado manual');
console.log('  - forceRestore() - Forzar restauración manual');

// ===============================================
// FUNCIONES PARA MANEJO DE PESTAÑAS CON FUNCIONALIDAD
// ===============================================

/**
 * Inicializa el sistema de pestañas con funcionalidad de guardado
 */
function initTabSystem() {
    console.log('🔧 Inicializando sistema de pestañas...');
    
    const tabButtons = document.querySelectorAll('.nav-tabs .nav-link');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Agregar event listeners a las pestañas
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetTab = button.getAttribute('data-bs-target')?.replace('#', '') || 
                             button.getAttribute('href')?.replace('#', '');
            
            if (targetTab) {
                // Guardar datos de la pestaña actual antes de cambiar
                if (autoSaveEnabled && consultaActual) {
                    saveCurrentTabData();
                }
                
                // Cambiar a la nueva pestaña
                switchTab(targetTab);
                currentTab = targetTab;
                
                // Cargar datos de la nueva pestaña
                loadTabData(targetTab);
            }
        });
    });
    
    console.log('✅ Sistema de pestañas inicializado');
}

/**
 * Cambia entre pestañas
 */
function switchTab(targetTabId) {
    // Remover clases activas
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        link.setAttribute('aria-selected', 'false');
    });
    
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('show', 'active');
    });
    
    // Activar nueva pestaña
    const targetButton = document.querySelector(`[data-bs-target="#${targetTabId}"], [href="#${targetTabId}"]`);
    const targetPane = document.getElementById(targetTabId);
    
    if (targetButton) {
        targetButton.classList.add('active');
        targetButton.setAttribute('aria-selected', 'true');
    }
    
    if (targetPane) {
        targetPane.classList.add('show', 'active');
    }
}

/**
 * Inicializa el sistema de autoguardado
 */
function initAutoSave() {
    console.log('🔧 Inicializando autoguardado...');
    
    // Event listeners para cambios en formularios
    document.addEventListener('input', function(e) {
        if (autoSaveEnabled && consultaActual && e.target.matches('input, textarea, select')) {
            // Debounce para evitar demasiadas llamadas
            clearTimeout(window.autoSaveTimeout);
            window.autoSaveTimeout = setTimeout(() => {
                saveCurrentTabData();
            }, 2000); // Guardar después de 2 segundos de inactividad
        }
    });
    
    // Inicializar indicador de autoguardado
    updateAutoSaveIndicator(false);
    
    console.log('✅ Autoguardado inicializado');
}

/**
 * Guarda los datos de la pestaña actual
 */
function saveCurrentTabData() {
    if (!consultaActual || !consultaActual.id) {
        console.warn('⚠️ saveCurrentTabData: No hay consulta actual para guardar o la consulta no tiene ID.', consultaActual);
        return;
    }
    
    console.log(`💾 Guardando datos de pestaña: ${currentTab}`);
    
    const tabData = collectTabData(currentTab);
    // Garantizar envío de revision_sistemas si estamos en la pestaña de motivo-consulta
    if (currentTab === 'motivo-consulta') {
        // Asegurar que se guarde la nota del sistema actualmente seleccionado
        const notasTextarea = document.querySelector('textarea[name="revision_sistemas_notas"]');
        if (sistemaSeleccionado && notasTextarea) {
            revisionSistemasData[sistemaSeleccionado] = notasTextarea.value;
        }
        // Construir texto final a partir de badges y textarea
        let revisionTexto = Object.entries(revisionSistemasData)
            .filter(([_, notas]) => (notas || '').trim() !== '')
            .map(([sistema, notas]) => `${sistema}: ${notas}`)
            .join('. ');
        // Fallback: si no hay badges usados, enviar lo que esté en el textarea
        if (!revisionTexto && notasTextarea) {
            revisionTexto = notasTextarea.value || '';
        }
        tabData['revision_sistemas'] = revisionTexto;
        // También incluir el valor crudo del textarea para compatibilidad backend
        if (notasTextarea && notasTextarea.value) {
            tabData['revision_sistemas_notas'] = notasTextarea.value;
        }
    }
    if (Object.keys(tabData).length === 0) {
        console.log('📝 No hay datos para guardar en esta pestaña');
        return;
    }
    
    // Determinar la URL según la pestaña, siempre usando .id
    let saveUrl = '';
    switch (currentTab) {
        case 'datos-generales':
            saveUrl = `/consulta/${consultaActual.id}/datos-generales`;
            break;
        case 'motivo-consulta':
            saveUrl = `/consulta/${consultaActual.id}/motivo`;
            break;
        case 'diagnostico':
            saveUrl = `/consulta/${consultaActual.id}/diagnostico-completo`;
            break;
        case 'receta':
            saveUrl = `/consulta/${consultaActual.id}/receta-completa`;
            break;
        default:
            console.warn(`⚠️ Pestaña no reconocida: ${currentTab}`);
            return;
    }
    
    // Enviar datos al servidor
    fetch(saveUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(tabData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            console.log('✅ Datos guardados:', data.message);
            showSaveNotification('Guardado automáticamente', 'success');
        } else if (data.error) {
            console.error('❌ Error al guardar:', data.error);
            showSaveNotification('Error al guardar: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('❌ Error de red al guardar:', error);
        showSaveNotification('Error de conexión', 'error');
    });
}

/**
 * Recolecta los datos de una pestaña específica
 */
function collectTabData(tabId) {
    const tabPane = document.getElementById(tabId);
    if (!tabPane) return {};
    
    const data = {};
    const formElements = tabPane.querySelectorAll('input, textarea, select');
    
    formElements.forEach(element => {
        if (element.name && element.value.trim() !== '') {
            data[element.name] = element.value.trim();
        }
    });
    
    return data;
}

/**
 * Carga los datos de una pestaña desde el servidor
 */
function loadTabData(tabId) {
    if (!consultaActual) return;
    
    // Esta función se puede expandir para cargar datos específicos
    // Por ahora, los datos se cargan cuando se selecciona el paciente
    console.log(`📖 Cargando datos para pestaña: ${tabId}`);
}

/**
 * Actualiza el indicador de autoguardado
 */
function updateAutoSaveIndicator(enabled) {
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.style.display = enabled ? 'inline-block' : 'none';
    }
    autoSaveEnabled = enabled;
}

/**
 * Muestra una notificación de guardado
 */
function showSaveNotification(message, type = 'success') {
    // Crear o actualizar notificación
    let notification = document.getElementById('save-notification');
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'save-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 4px;
            color: white;
            font-size: 14px;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        document.body.appendChild(notification);
    }
    
    // Establecer color según tipo
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107'
    };
    
    notification.style.backgroundColor = colors[type] || colors.success;
    notification.textContent = message;
    notification.style.opacity = '1';
    
    // Ocultar después de 3 segundos
    setTimeout(() => {
        notification.style.opacity = '0';
    }, 3000);
}

/**
 * Obtiene el token CSRF
 */
function getCSRFToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    return token ? token.value : '';
}

/**
 * Habilita el autoguardado para una consulta específica
 */
function enableAutoSaveForConsulta(consulta) {
    if (consulta && consulta.id) {
        consultaActual = consulta; // Guardar el objeto completo
        updateAutoSaveIndicator(true);
        showFormControls();
        console.log(`🔄 Autoguardado habilitado para consulta ID: ${consulta.id}`);
    } else {
        console.error("Error: se intentó habilitar el autoguardado sin una consulta válida.", consulta);
        disableAutoSave();
    }
}

/**
 * Deshabilita el autoguardado
 */
function disableAutoSave() {
    consultaActual = null;
    updateAutoSaveIndicator(false);
    
    // Ocultar controles de formulario
    hideFormControls();
    
    console.log('⏸️ Autoguardado deshabilitado');
}

/**
 * Funciones auxiliares para mostrar/ocultar controles
 */
function showFormControls() {
    const limpiarBtn = document.getElementById('btn-limpiar-formulario');
    const debugBtn = document.getElementById('btn-debug-autosave');
    
    if (limpiarBtn) limpiarBtn.style.display = 'inline-block';
    if (debugBtn) debugBtn.style.display = 'inline-block';
}

function hideFormControls() {
    const limpiarBtn = document.getElementById('btn-limpiar-formulario');
    const debugBtn = document.getElementById('btn-debug-autosave');
    
    if (limpiarBtn) limpiarBtn.style.display = 'none';
    if (debugBtn) debugBtn.style.display = 'none';
}

/**
 * Función para limpiar formulario
 */
function limpiarFormulario() {
    if (confirm('¿Está seguro de que desea limpiar todos los campos del formulario?')) {
        const currentTabPane = document.getElementById(currentTab);
        if (currentTabPane) {
            const formElements = currentTabPane.querySelectorAll('input, textarea, select');
            formElements.forEach(element => {
                if (element.type !== 'hidden') {
                    element.value = '';
                }
            });
            showSaveNotification('Formulario limpiado', 'warning');
        }
    }
}

/**
 * Busca o crea una consulta para el paciente
 */
function findOrCreateConsultaForPatient(patient) {
    console.log("findOrCreateConsultaForPatient -> ", patient);

    const historial = Array.isArray(patient.historial_consultas) ? patient.historial_consultas : [];
    // Buscar consulta en progreso para no sobrescribir consultas completadas
    let consultaActiva = historial.find(c => c.estado === 'en_progreso');

    if (consultaActiva) {
        if (!consultaActiva.id) {
            alert("Error: la consulta activa no tiene un campo 'id'. Revisa el backend.\nObjeto consulta: " + JSON.stringify(consultaActiva));
        }
        console.log("Consulta en progreso encontrada:", consultaActiva);
        enableAutoSaveForConsulta(consultaActiva);
        loadPatientDataInTabs(consultaActiva);
        return;
    }

    // No hay consulta en progreso: crear una nueva (AJAX) enviando el tipo si está marcado en recepción
    const tipoSeleccionado = document.querySelector('input[name="tipo_consulta"]:checked')?.value || null;
    fetch(`/consulta/nueva_ajax/${patient.id}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tipo_consulta: tipoSeleccionado })
    })
    .then(response => response.json())
    .then(result => {
        if (result && result.success && result.consulta && result.consulta.id) {
            const data = result.consulta;
            consultaActiva = data;
            consultaActual = data;
            // Insertar la nueva consulta al inicio del historial del paciente en memoria
            if (!Array.isArray(window.currentPatient.historial_consultas)) {
                window.currentPatient.historial_consultas = [];
            }
            window.currentPatient.historial_consultas.unshift({
                id: data.id,
                fecha: data.fecha,
                tipo_consulta: data.tipo_consulta,
                medico: '',
                motivo_consulta: '',
                historia_enfermedad: '',
                revision_sistemas: '',
                antecedentes: '',
                diagnostico: '',
                tratamiento: '',
                estado: data.estado,
                signos_vitales: null
            });
            // Actualizar panel de historial en UI
            updateMedicalHistory(window.currentPatient);
            enableAutoSaveForConsulta(data);
            loadPatientDataInTabs(data);
        } else {
            alert('No se pudo crear una consulta activa para este paciente.');
        }
    })
    .catch(error => {
        console.error('Error al crear nueva consulta:', error);
        alert('No se pudo crear una consulta activa para este paciente.');
    });
}

/**
 * Actualiza los campos de datos generales con información del paciente
 */
function updateGeneralDataFields(patient) {
    console.log('📝 Actualizando campos de datos generales...');
    
    // Mapear campos del paciente a inputs del formulario
    const fieldMappings = {
        'estado_civil': patient.estado_civil,
        'religion': patient.religion,
        'escolaridad': patient.escolaridad,
        'ocupacion': patient.ocupacion,
        'procedencia': patient.procedencia,
        'numero_expediente': patient.numero_expediente,
        'direccion': patient.direccion,
        'telefono': patient.telefono
    };
    
    // Actualizar cada campo si existe
    Object.entries(fieldMappings).forEach(([fieldName, value]) => {
        const field = document.querySelector(`input[name="${fieldName}"], textarea[name="${fieldName}"]`);
        if (field && value) {
            field.value = value;
            console.log(`✅ Campo ${fieldName} actualizado:`, value);
        }
    });

    // La visibilidad de antecedentes se controla desde la función local en selectPatient
}




/**
 * Carga los datos del paciente en todas las pestañas
 */
function loadPatientDataInTabs(consulta) {
    console.log('📖 Cargando datos de consulta en pestañas:', consulta);
    
    // Cargar datos en pestaña Motivo Consulta
    if (consulta.motivo_consulta) {
        const motivoField = document.querySelector('textarea[name="motivo_consulta"]');
        if (motivoField) motivoField.value = consulta.motivo_consulta;
    }
    
    if (consulta.historia_enfermedad) {
        const historiaField = document.querySelector('textarea[name="historia_enfermedad"]');
        if (historiaField) historiaField.value = consulta.historia_enfermedad;
    }
    
    if (consulta.revision_sistemas) {
        const revisionField = document.querySelector('textarea[name="revision_sistemas_notas"]');
        if (revisionField) revisionField.value = consulta.revision_sistemas;
    }
    
    // Cargar antecedentes gineco-obstétricos solo para pacientes femeninos
    if (window.currentPatient && window.currentPatient.genero === 'Femenino') {
        const antecedenteFields = ['gestas', 'partos', 'abortos', 'hijos_vivos', 'hijos_muertos'];
        antecedenteFields.forEach(fieldName => {
            if (consulta[fieldName]) {
                const field = document.querySelector(`input[name="${fieldName}"]`);
                if (field) field.value = consulta[fieldName];
            }
        });
        
        if (consulta.fecha_ultima_regla) {
            const fechaField = document.querySelector('input[name="fecha_ultima_regla"]');
            if (fechaField) fechaField.value = consulta.fecha_ultima_regla;
        }
    }
    
    if (consulta.antecedentes) {
        const antecedentesField = document.querySelector('textarea[name="antecedentes"]');
        if (antecedentesField) antecedentesField.value = consulta.antecedentes;
    }
    
    // Cargar datos de examen físico
    const examenFields = ['presion_arterial_examen', 'frecuencia_respiratoria_examen', 'temperatura_examen', 
                         'peso', 'talla', 'frecuencia_cardiaca_examen', 'saturacion_oxigeno', 'imc'];
    examenFields.forEach(fieldName => {
        if (consulta[fieldName.replace('_examen', '')]) {
            const field = document.querySelector(`input[name="${fieldName}"]`);
            if (field) field.value = consulta[fieldName.replace('_examen', '')];
        }
    });
    
    // Cargar datos de diagnóstico
    if (consulta.diagnostico) {
        const diagnosticoField = document.querySelector('textarea[name="diagnostico"]');
        if (diagnosticoField) diagnosticoField.value = consulta.diagnostico;
        // También en la receta
        const diagnosticoRecetaInput = document.getElementById('receta-diagnostico-input');
        if (diagnosticoRecetaInput) diagnosticoRecetaInput.value = consulta.diagnostico;
    }
    
    if (consulta.laboratorio) {
        const laboratorioField = document.querySelector('textarea[name="laboratorio"]');
        if (laboratorioField) laboratorioField.value = consulta.laboratorio;
    }
    
    // Cargar datos de receta
    if (consulta.tratamiento) {
        // Parsear el tratamiento para extraer medicamento, dosificación e indicaciones
        const tratamientoLines = consulta.tratamiento.split('\n');
        tratamientoLines.forEach(line => {
            if (line.startsWith('Medicamento:')) {
                const medicamentoField = document.querySelector('input[name="medicamento"]');
                if (medicamentoField) medicamentoField.value = line.replace('Medicamento:', '').trim();
            }
            if (line.startsWith('Dosificación:')) {
                const dosificacionField = document.querySelector('input[name="dosificacion"]');
                if (dosificacionField) dosificacionField.value = line.replace('Dosificación:', '').trim();
            }
            if (line.startsWith('Indicaciones:')) {
                const indicacionesField = document.querySelector('textarea[name="indicaciones"]');
                if (indicacionesField) indicacionesField.value = line.replace('Indicaciones:', '').trim();
            }
        });
    }
}

/**
 * Actualiza la información del paciente en la pestaña de receta
 */
function updateRecetaPatientInfo(patient) {
    const nombreElement = document.getElementById('receta-paciente-nombre');
    const edadElement = document.getElementById('receta-paciente-edad');
    
    if (nombreElement) {
        nombreElement.textContent = patient.nombre_completo || 'Paciente no seleccionado';
    }
    
    if (edadElement) {
        edadElement.textContent = patient.edad ? `${patient.edad} años` : '-- años';
    }
    
    // El diagnóstico se actualizará cuando se carguen los datos de la consulta
}

/**
 * Guarda los datos generales del paciente
 */
function guardarDatosGenerales() {
    if (!consultaActual || !consultaActual.id) {
        console.error('Error: No se puede guardar. consultaActual no está definida o no tiene ID.', consultaActual);
        alert('Debe seleccionar un paciente y tener una consulta activa');
        return;
    }

    const datos = {
        estado_civil: document.querySelector('input[name="estado_civil"]')?.value || '',
        dni: document.querySelector('input[name="dni"]')?.value || '',
        religion: document.querySelector('input[name="religion"]')?.value || '',
        escolaridad: document.querySelector('input[name="escolaridad"]')?.value || '',
        ocupacion: document.querySelector('input[name="ocupacion"]')?.value || '',
        direccion: document.querySelector('input[name="direccion"]')?.value || '',
        procedencia: document.querySelector('input[name="procedencia"]')?.value || '',
        telefono: document.querySelector('input[name="telefono"]')?.value || '',
        numero_expediente: document.querySelector('input[name="numero_expediente"]')?.value || ''
    };

    const btn = document.getElementById('btn-guardar-datos-generales');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
    }

    fetch(`/consulta/${consultaActual.id}/datos-generales`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            mostrarNotificacion('success', data.message);
        } else if (data.error) {
            mostrarNotificacion('error', data.error);
        }
    })
    .catch(error => {
        console.error('Error al guardar datos generales:', error);
        mostrarNotificacion('error', 'Error al guardar los datos generales');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save me-1"></i>Guardar Datos Generales';
        }
    });
}

/**
 * Guarda el motivo de consulta y datos relacionados
 */
function guardarMotivoConsulta() {
    if (!consultaActual || !consultaActual.id) {
        console.error('Error: No se puede guardar. consultaActual no está definida o no tiene ID.', consultaActual);
        alert('Debe seleccionar un paciente y tener una consulta activa');
        return;
    }

    // Guardar la nota del sistema actual antes de construir el texto final
    const notasTextarea = document.querySelector('textarea[name="revision_sistemas_notas"]');
    if (sistemaSeleccionado && notasTextarea) {
        revisionSistemasData[sistemaSeleccionado] = notasTextarea.value;
    }

    // Formatear los datos de revisión por sistemas
    let revisionSistemasTexto = Object.entries(revisionSistemasData)
        .filter(([_, notas]) => notas.trim() !== '')
        .map(([sistema, notas]) => `${sistema}: ${notas}`)
        .join('. ');

    const datos = {
        motivo_consulta: document.querySelector('textarea[name="motivo_consulta"]')?.value || '',
        historia_enfermedad: document.querySelector('textarea[name="historia_enfermedad"]')?.value || '',
        revision_sistemas: revisionSistemasTexto,
        antecedentes: document.querySelector('textarea[name="antecedentes"]')?.value || '',
        presion_arterial_examen: document.querySelector('input[name="presion_arterial_examen"]')?.value || '',
        frecuencia_respiratoria_examen: document.querySelector('input[name="frecuencia_respiratoria_examen"]')?.value || '',
        temperatura_examen: document.querySelector('input[name="temperatura_examen"]')?.value || '',
        peso: document.querySelector('input[name="peso"]')?.value || '',
        talla: document.querySelector('input[name="talla"]')?.value || '',
        frecuencia_cardiaca_examen: document.querySelector('input[name="frecuencia_cardiaca_examen"]')?.value || '',
        saturacion_oxigeno: document.querySelector('input[name="saturacion_oxigeno"]')?.value || '',
        imc: document.querySelector('input[name="imc"]')?.value || ''
    };

    // Incluir campos gineco-obstétricos solo para pacientes femeninos
    if (window.currentPatient && window.currentPatient.genero === 'Femenino') {
        datos.gestas = document.querySelector('input[name="gestas"]')?.value || '';
        datos.partos = document.querySelector('input[name="partos"]')?.value || '';
        datos.abortos = document.querySelector('input[name="abortos"]')?.value || '';
        datos.hijos_vivos = document.querySelector('input[name="hijos_vivos"]')?.value || '';
        datos.hijos_muertos = document.querySelector('input[name="hijos_muertos"]')?.value || '';
        datos.fecha_ultima_regla = document.querySelector('input[name="fecha_ultima_regla"]')?.value || '';
    }

    const btn = document.getElementById('btn-guardar-motivo-consulta');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
    }

    fetch(`/consulta/${consultaActual.id}/motivo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            mostrarNotificacion('success', data.message);
        } else if (data.error) {
            mostrarNotificacion('error', data.error);
        }
    })
    .catch(error => {
        console.error('Error al guardar motivo de consulta:', error);
        mostrarNotificacion('error', 'Error al guardar el motivo de consulta');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save me-1"></i>Guardar Motivo de Consulta';
        }
    });
}

/**
 * Guarda el diagnóstico
 */
function guardarDiagnostico() {
    if (!consultaActual || !consultaActual.id) {
        console.error('Error: No se puede guardar. consultaActual no está definida o no tiene ID.', consultaActual);
        alert('Debe seleccionar un paciente y tener una consulta activa');
        return;
    }

    const datos = {
        diagnostico: document.querySelector('textarea[name="diagnostico"]')?.value || '',
        laboratorio: document.querySelector('textarea[name="laboratorio"]')?.value || ''
    };

    const btn = document.getElementById('btn-guardar-diagnostico');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Guardando...';
    }

    fetch(`/consulta/${consultaActual.id}/diagnostico-completo`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            mostrarNotificacion('success', data.message);
            // Actualizar el diagnóstico en la pestaña de receta
            const diagnosticoRecetaInput = document.getElementById('receta-diagnostico-input');
            if (diagnosticoRecetaInput && datos.diagnostico) {
                diagnosticoRecetaInput.value = datos.diagnostico;
            }
        } else if (data.error) {
            mostrarNotificacion('error', data.error);
        }
    })
    .catch(error => {
        console.error('Error al guardar diagnóstico:', error);
        mostrarNotificacion('error', 'Error al guardar el diagnóstico');
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-save me-1"></i>Guardar Diagnóstico';
        }
    });
}

/**
 * Guarda la receta médica
 */
function guardarReceta() {
    if (!consultaActual || !consultaActual.id) {
        alert('Debe seleccionar un paciente con una consulta activa para guardar.');
        return Promise.reject('No hay consulta activa');
    }

    const datos = {
        medicamentos: document.querySelector('textarea[name="medicamentos"]')?.value || '',
        indicaciones: document.querySelector('textarea[name="indicaciones"]')?.value || '',
        diagnostico: document.querySelector('#receta-diagnostico-input')?.value || document.querySelector('textarea[name="diagnostico"]')?.value || '',
        medicamento: document.querySelector('input[name="medicamento"]')?.value || '',
        dosificacion: document.querySelector('input[name="dosificacion"]')?.value || ''
    };

    console.log("Guardando datos de receta:", datos);

    return fetch(`/consulta/${consultaActual.id}/receta-guardar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(datos)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            mostrarNotificacion('success', 'Receta guardada exitosamente');
            return true;
        } else {
            throw new Error(data.error || 'Error desconocido al guardar la receta');
        }
    })
    .catch(error => {
        console.error('❌ Error al guardar receta:', error);
        mostrarNotificacion('error', `Error al guardar la receta: ${error.message}`);
        return false;
    });
}

// Nueva función para imprimir como PDF
async function imprimirReceta() {
    const btn = document.getElementById('btn-imprimir-receta');
    if (!btn) return;

    if (!consultaActual || !consultaActual.id) {
        alert('Por favor, seleccione un paciente con una consulta activa antes de imprimir.');
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';

    try {
        const guardadoExitoso = await guardarReceta();
        
        if (guardadoExitoso) {
            btn.innerHTML = '<i class="fas fa-print"></i> Generando PDF...';
            // Pequeña pausa para asegurar que el guardado se procese
            setTimeout(() => {
                const url = `/generar_receta_pdf/${consultaActual.id}`;
                window.open(url, '_blank');
            }, 500);
        } else {
            alert('No se pudo guardar la receta antes de generar el PDF. Revise los datos y la conexión.');
        }
    } catch (error) {
        alert('Ocurrió un error al intentar guardar o imprimir la receta.');
        console.error(error);
    } finally {
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-print me-1"></i> IMPRIMIR';
        }, 2000);
    }
}


/**
 * Muestra una notificación en pantalla
 */
function mostrarNotificacion(tipo, mensaje) {
    // Crear elemento de notificación
    const notificacion = document.createElement('div');
    notificacion.className = `alert alert-${tipo === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    notificacion.style.position = 'fixed';
    notificacion.style.top = '20px';
    notificacion.style.right = '20px';
    notificacion.style.zIndex = '9999';
    notificacion.style.minWidth = '300px';
    
    notificacion.innerHTML = `
        <i class="fas fa-${tipo === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notificacion);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        if (notificacion.parentNode) {
            notificacion.remove();
        }
    }, 5000);
}

function initRevisionSistemas() {
    const container = document.getElementById('sistemas-badges-container');
    const notasTextarea = document.querySelector('textarea[name="revision_sistemas_notas"]');

    if (container && notasTextarea) {
        container.addEventListener('click', function(e) {
            if (e.target.classList.contains('system-badge')) {
                const sistemaActual = e.target.dataset.system;

                // Guardar la nota del sistema anteriormente seleccionado
                if (sistemaSeleccionado && sistemaSeleccionado !== sistemaActual) {
                    revisionSistemasData[sistemaSeleccionado] = notasTextarea.value;
                }
                
                // Si se hace clic en el mismo, se deselecciona
                if (e.target.classList.contains('active')) {
                    e.target.classList.remove('active', 'bg-primary');
                    e.target.classList.add('bg-secondary');
                    notasTextarea.value = '';
                    sistemaSeleccionado = null;
                } else {
                    // Deseleccionar todos los demás
                    container.querySelectorAll('.system-badge').forEach(badge => {
                        badge.classList.remove('active', 'bg-primary');
                        badge.classList.add('bg-secondary');
                    });

                    // Seleccionar el actual
                    e.target.classList.add('active', 'bg-primary');
                    e.target.classList.remove('bg-secondary');
                    
                    // Cargar la nota del sistema actual
                    notasTextarea.value = revisionSistemasData[sistemaActual] || '';
                    sistemaSeleccionado = sistemaActual;
                }
            }
        });
    }
}

/**
 * Obtiene el token CSRF de la etiqueta meta en el HTML
 */
function getCSRFToken() {
    const tokenTag = document.querySelector('meta[name="csrf-token"]');
    if (tokenTag) {
        return tokenTag.getAttribute('content');
    }
    console.error('CSRF token not found: Asegúrese de que la etiqueta meta "csrf-token" está en su base.html.');
    return '';
}

// Descargar PDF de una consulta específica
window.descargarConsultaPDF = function(consultaId) {
    if (!consultaId) return;
    const url = `/generar_consulta_pdf/${consultaId}`;
    window.open(url, '_blank');
};

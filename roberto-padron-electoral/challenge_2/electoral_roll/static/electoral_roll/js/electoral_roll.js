(() => {

    const searchByNameDiv = document.querySelector("#searchByNameDiv");
    const identification = document.querySelector("#identification");
    const formLegend = document.querySelector("#formLegend");
    const searchBtn = document.querySelector("#actionBtn");
    const searchByName = document.querySelector("#searchByNameRadio");
    const searchById = document.querySelector("#searchByIdRadio");
    const id_nombre = document.querySelector("#id_nombre");
    const id_primer_apellido = document.querySelector("#id_primer_apellido");
    const id_segundo_apellido = document.querySelector("#id_segundo_apellido");
    const id_cedula = document.querySelector("#id_cedula");
    const radioOption = document.querySelector("#radioOption");
    const chargeSpan = document.querySelector("#chargeSpan");
    const btnAdd = document.querySelector("#btnAdd");


    const searchByNameText = "Ingresa tu nombre completo (no uses tíldes)";
    const searchByIdText = "Ingresa tu número de cédula";

    const isChecked = (input, legend, option, text, btn) => {
        if (input.checked) {
            if (input == searchById) {
                requiredId(true);
                requiredName(false);
            }
            else if (input == searchByName) {
                requiredId(false);
                requiredName(true);
            }
            legend.innerHTML = text;
            option.style.display = 'block';
            btn.disabled = false;
        }
        else {
            option.style.display = 'none';
        }

    };

    const requiredName = (value) => {
        id_segundo_apellido.required = value;
        id_primer_apellido.required = value;
        id_nombre.required = value;
    };

    const requiredId = (value) => {
        id_cedula.required = value;
    };

    const events = () => {
        if (searchBtn) {
            searchByName.addEventListener('click', (event) => {
                if (event.target.checked == true) {
                    formLegend.innerHTML = searchByNameText;
                    searchByNameDiv.style.display = 'block';
                    identification.style.display = 'none';
                    radioOption.value = searchByName.value;
                    requiredId(false);
                    requiredName(true);
                    searchBtn.disabled = false;
                }
            });

            searchById.addEventListener('click', (event) => {
                if (event.target.checked == true) {
                    formLegend.innerHTML = searchByIdText;
                    identification.style.display = 'block';
                    searchByNameDiv.style.display = 'none';
                    radioOption.value = searchById.value;
                    searchBtn.disabled = false;
                    requiredId(true);
                    requiredName(false);
                }
            });

            searchBtn.addEventListener('click', () => {

                if (radioOption.value == 1) {
                    if (id_nombre.value.length > 0 && id_primer_apellido.value.length > 0 && id_segundo_apellido.value.length > 0) {
                        searchBtn.innerHTML = 'Buscando <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="chargeSpan"></span>';
                    }
                }
                else if (radioOption.value == 2) {
                    if (id_cedula.value.length > 0) {
                        searchBtn.innerHTML = 'Buscando <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="chargeSpan"></span>';

                    }
                }
            });
        }

        if (btnAdd) {
            btnAdd.addEventListener('click', () => {
                btnAdd.innerHTML = 'Agregando <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true" id="chargeSpan"></span>';
            });
        }


        window.addEventListener("pageshow", function (event) {
            var historyTraversal = event.persisted ||
                (typeof window.performance != "undefined" &&
                    window.performance.navigation.type === 2);
            if (historyTraversal) {
                // Handle page restore.
                window.location.reload();
            }
        });

    };


    const init = () => {
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = "Buscar";
            isChecked(searchById, formLegend, identification, searchByIdText, searchBtn);
            isChecked(searchByName, formLegend, searchByNameDiv, searchByNameText, searchBtn);
        }
        if (btnAdd) {
            btnAdd.innerHTML = "Agregar";
        }
        events();
    };


    init();


})();
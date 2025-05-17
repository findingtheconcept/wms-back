document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;

    // --- ОБЩИЕ ФУНКЦИИ ---
    const apiBaseUrl = '/api';

    async function fetchData(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `Ошибка HTTP: ${response.status}` }));
                console.error('Ошибка API:', errorData);
                alert(`Ошибка: ${errorData.error || response.statusText}`);
                return null;
            }
            if (response.status === 204) return true; // No content
            return await response.json();
        } catch (error) {
            console.error('Сетевая ошибка или ошибка парсинга JSON:', error);
            alert('Произошла сетевая ошибка. Пожалуйста, проверьте ваше соединение.');
            return null;
        }
    }

    function populateSelect(selectElement, items, valueField, textField, placeholder) {
        if (!selectElement) return;
        selectElement.innerHTML = ''; // Очистить существующие опции
        if (placeholder) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = "";
            placeholderOption.textContent = placeholder;
            placeholderOption.disabled = true;
            placeholderOption.selected = true;
            selectElement.appendChild(placeholderOption);
        }
        items.forEach(item => {
            const option = document.createElement('option');
            //option.value = item[valueField];
            option.value = item[textField];
            option.textContent = item[textField];
            selectElement.appendChild(option);
        });
    }

    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div class="toast align-items-center text-bg-${type === 'success' ? 'primary' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}" data-bs-delay="3000">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1090'; // Выше модальных окон Bootstrap
        document.body.appendChild(container);
        return container;
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ВХОДА (login.html) ---
    if (currentPath.includes('/login')) {
        const loginForm = document.querySelector('form'); // Предполагаем, что на странице одна форма
        if (loginForm) {
            loginForm.addEventListener('submit', async (event) => {
                // Предотвращаем стандартную отправку формы, так как Flask сам обработает
                // event.preventDefault();
                // const formData = new FormData(loginForm);
                // const response = await fetch('/login', { // Отправляем на Flask маршрут
                //     method: 'POST',
                //     body: formData
                // });
                // if (response.ok) {
                //     const result = await response.json().catch(() => ({})); // или response.text() если редирект
                //     if (result.success || response.redirected) {
                //         window.location.href = result.redirect_url || '/products';
                //     } else {
                //         alert(result.error || 'Ошибка входа. Попробуйте снова.');
                //     }
                // } else {
                //     alert('Ошибка сервера при попытке входа.');
                // }
                // Закомментировано, т.к. Flask будет обрабатывать POST и делать редирект или рендерить с ошибкой.
                // JS здесь не нужен для отправки, если форма стандартная.
            });
        }
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ СПИСКА ТОВАРОВ (index.html) ---
    if (currentPath.includes('/products') || currentPath === '/') {
        const productTableBody = document.querySelector('#productTableBody'); // Добавьте id="productTableBody" к tbody в index.html
        const addProductForm = document.getElementById('addProductForm');
        const editProductForm = document.getElementById('editProductForm');
        const deleteProductModalElement = document.getElementById('deleteProductModal');
        const deleteProductConfirmButton = deleteProductModalElement ? deleteProductModalElement.querySelector('.btn-danger') : null;
        let currentProductIdToDelete = null;
        let currentProductToEdit = null;

        const addProductCategorySelect = document.getElementById('addProductCategory');
        const editProductCategorySelect = document.getElementById('editProductCategory');
        const filterCategorySelect = document.getElementById('filterCategory');

        const registerIncomingForm = document.getElementById('registerIncomingForm');
        const registerOutgoingForm = document.getElementById('registerOutgoingForm');
        const incomingProductSelect = document.getElementById('incomingProduct');
        const outgoingProductSelect = document.getElementById('outgoingProduct');


        async function loadCategoriesForForms() {
            const categories = await fetchData(`${apiBaseUrl}/categories`);
            if (categories) {
                populateSelect(addProductCategorySelect, categories, 'id', 'name', 'Выберите категорию...');
                populateSelect(editProductCategorySelect, categories, 'id', 'name', 'Выберите категорию...');
                populateSelect(filterCategorySelect, [{id: "", name: "Все категории"}, ...categories], 'id', 'name');
                populateSelect(incomingProductSelect, [], 'id', 'name', 'Сначала загрузите товары...'); // Товары будут позже
                populateSelect(outgoingProductSelect, [], 'id', 'name', 'Сначала загрузите товары...');
            }
        }

        async function loadProductsForOperationForms(products) {
             if (products) {
                populateSelect(incomingProductSelect, products, 'id', 'name', 'Выберите товар...');
                populateSelect(outgoingProductSelect, products, 'id', 'name', 'Выберите товар...');
            }
        }


        function renderProducts(products) {
            if (!productTableBody) return;
            productTableBody.innerHTML = ''; // Очищаем таблицу
            if (!products || products.length === 0) {
                productTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Товары не найдены.</td></tr>';
                return;
            }
            products.forEach(product => {
                const row = productTableBody.insertRow();
                row.dataset.productId = product.id;
                row.innerHTML = `
                    <td>${product.name}</td>
                    <td>${product.category_name}</td>
                    <td>${product.unit}</td>
                    <td>${product.location}</td>
                    <td>${product.min_stock}</td>
                    <td>${product.current_stock} ${product.current_stock < product.min_stock ? '<i class="bi bi-exclamation-triangle-fill text-danger ms-1" title="Остаток ниже минимума"></i>' : ''}</td>
                    <td class="action-icons">
                        <a href="#" class="edit-product" title="Редактировать" data-bs-toggle="modal" data-bs-target="#editProductModal"><i class="bi bi-pencil-square"></i></a>
                        <a href="#" class="delete-product" title="Удалить" data-bs-toggle="modal" data-bs-target="#deleteProductModal"><i class="bi bi-trash3-fill"></i></a>
                    </td>
                `;
            });
        }

        async function fetchAndRenderProducts() {
            const products = await fetchData(`${apiBaseUrl}/products`);
            if (products) {
                renderProducts(products);
                loadProductsForOperationForms(products); // Загружаем товары в селекты форм операций
            }
        }

        // Добавление товара
        if (addProductForm) {
            addProductForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(addProductForm);
                const productData = Object.fromEntries(formData.entries());
                // current_stock не задаем при создании, пусть будет 0 по умолчанию или через поступление
                productData.current_stock = 0; // Установим по умолчанию 0, или можно добавить поле в форму

                const result = await fetchData(`${apiBaseUrl}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });
                if (result && result.id) {
                    showToast('Товар успешно добавлен!');
                    fetchAndRenderProducts(); // Обновляем список
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
                    modal.hide();
                    addProductForm.reset();
                } else {
                    showToast(result ? result.error : 'Ошибка при добавлении товара.', 'danger');
                }
            });
        }

        // Редактирование товара - открытие модального окна и заполнение
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.edit-product')) {
                e.preventDefault();
                const row = e.target.closest('tr');
                const productId = parseInt(row.dataset.productId);
                currentProductToEdit = await fetchData(`${apiBaseUrl}/products/${productId}`);
                if (currentProductToEdit && editProductForm) {
                    document.getElementById('editingProductName').textContent = currentProductToEdit.name;
                    editProductForm.elements['name'].value = currentProductToEdit.name;
                    editProductForm.elements['category_id'].value = currentProductToEdit.category_id;
                    editProductForm.elements['unit'].value = currentProductToEdit.unit;
                    editProductForm.elements['description'].value = currentProductToEdit.description;
                    editProductForm.elements['location'].value = currentProductToEdit.location;
                    editProductForm.elements['min_stock'].value = currentProductToEdit.min_stock;
                    // current_stock не редактируем напрямую здесь, оно меняется через операции
                    // editProductForm.elements['current_stock'].value = currentProductToEdit.current_stock;
                }
            }
        });

        // Сохранение изменений товара
        if (editProductForm) {
            editProductForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (!currentProductToEdit) return;

                const formData = new FormData(editProductForm);
                const updatedData = Object.fromEntries(formData.entries());
                updatedData.category_id = parseInt(updatedData.category_id);
                updatedData.min_stock = parseInt(updatedData.min_stock);
                // updatedData.current_stock = parseInt(updatedData.current_stock); // Если разрешаем редактировать

                const result = await fetchData(`${apiBaseUrl}/products/${currentProductToEdit.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                });
                if (result && result.id) {
                    showToast('Товар успешно обновлен!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editProductModal'));
                    modal.hide();
                } else {
                     showToast(result ? result.error : 'Ошибка при обновлении товара.', 'danger');
                }
            });
        }

        // Удаление товара - открытие модального окна
         document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-product')) {
                e.preventDefault();
                const row = e.target.closest('tr');
                currentProductIdToDelete = parseInt(row.dataset.productId);
                const productName = row.cells[0].textContent;
                if (deleteProductModalElement) {
                    deleteProductModalElement.querySelector('#productNameToDelete').textContent = productName;
                }
            }
        });

        // Подтверждение удаления
        if (deleteProductConfirmButton) {
            deleteProductConfirmButton.addEventListener('click', async () => {
                if (currentProductIdToDelete === null) return;
                const result = await fetchData(`${apiBaseUrl}/products/${currentProductIdToDelete}`, {
                    method: 'DELETE'
                });
                if (result) { // Успешное удаление возвращает 204 No Content, или сообщение
                    showToast(result.message || 'Товар успешно удален!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(deleteProductModalElement);
                    modal.hide();
                    currentProductIdToDelete = null;
                } else {
                    showToast(result ? result.error : 'Ошибка при удалении товара.', 'danger');
                }
            });
        }

        // Регистрация поступления
        if (registerIncomingForm) {
            registerIncomingForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(registerIncomingForm);
                const operationData = {
                    type: "Поступление",
                    product_id: parseInt(formData.get('product_id')),
                    quantity: parseInt(formData.get('quantity')),
                    date: formData.get('date'), // Flask сам поставит текущую, если не передать
                    invoice_number: formData.get('invoice_number'),
                    party: formData.get('supplier'), // Используем поле поставщика
                    comment: formData.get('comment')
                };

                const result = await fetchData(`${apiBaseUrl}/operations/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operationData)
                });

                if (result && result.id) {
                    showToast('Поступление успешно зарегистрировано!');
                    fetchAndRenderProducts(); // Обновить остатки в таблице товаров
                    // Можно также обновить таблицу операций, если она на этой же странице или перейти на нее
                    const modal = bootstrap.Modal.getInstance(document.getElementById('registerIncomingModal'));
                    modal.hide();
                    registerIncomingForm.reset();
                } else {
                    showToast(result ? result.error : 'Ошибка регистрации поступления.', 'danger');
                }
            });
        }

        // Регистрация отгрузки
        if (registerOutgoingForm) {
            registerOutgoingForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(registerOutgoingForm);
                 const operationData = {
                    type: "Отгрузка",
                    product_id: parseInt(formData.get('product_id')),
                    quantity: parseInt(formData.get('quantity')),
                    date: formData.get('date'),
                    invoice_number: formData.get('invoice_number'),
                    party: formData.get('recipient'), // Используем поле получателя
                    comment: formData.get('comment')
                };
                const result = await fetchData(`${apiBaseUrl}/operations/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(operationData)
                });

                if (result && result.id) {
                    showToast('Отгрузка успешно зарегистрирована!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(document.getElementById('registerOutgoingModal'));
                    modal.hide();
                    registerOutgoingForm.reset();
                } else {
                    showToast(result ? result.error : 'Ошибка регистрации отгрузки.', 'danger');
                }
            });
        }


        // Инициализация: загрузка категорий и товаров
        loadCategoriesForForms().then(() => {
            fetchAndRenderProducts();
        });

        // Логика для фильтров (упрощенная, на клиенте)
        const searchNameInput = document.getElementById('searchName');
        const filterLocationInput = document.getElementById('filterLocation');
        const filterAvailabilitySelect = document.getElementById('filterAvailability');
        const filterMinStockCheckbox = document.getElementById('filterMinStock');
        const filterButton = document.querySelector('.card-header button'); // Если есть кнопка "Применить фильтр"

        function applyFilters() {
            const searchTerm = searchNameInput.value.toLowerCase();
            const categoryFilter = filterCategorySelect.value;
            const locationFilter = filterLocationInput.value.toLowerCase();
            const availabilityFilter = filterAvailabilitySelect.value;
            const minStockFilter = filterMinStockCheckbox.checked;

            let products = JSON.parse(JSON.stringify(window.originalProducts || [])); // Работаем с копией

            if (searchTerm) {
                products = products.filter(p => p.name.toLowerCase().includes(searchTerm));
            }
            if (categoryFilter) {
                products = products.filter(p => p.category_id == categoryFilter);
            }
            if (locationFilter) {
                products = products.filter(p => p.location && p.location.toLowerCase().includes(locationFilter));
            }
            if (availabilityFilter === "in_stock") {
                products = products.filter(p => p.current_stock > 0);
            } else if (availabilityFilter === "out_of_stock") {
                products = products.filter(p => p.current_stock <= 0);
            }
            if (minStockFilter) {
                products = products.filter(p => p.current_stock < p.min_stock);
            }
            renderProducts(products);
        }

        async function initialLoadAndStore() {
            const products = await fetchData(`${apiBaseUrl}/products`);
            if (products) {
                window.originalProducts = products; // Сохраняем оригинальный список
                renderProducts(products);
                loadProductsForOperationForms(products);
            }
        }

        // Перезагружаем оригинальные данные при загрузке страницы
         loadCategoriesForForms().then(() => {
            initialLoadAndStore();
        });

        // Навешиваем обработчики на изменения фильтров
        [searchNameInput, filterCategorySelect, filterLocationInput, filterAvailabilitySelect, filterMinStockCheckbox].forEach(el => {
            if (el) el.addEventListener('input', applyFilters); // 'input' для текстовых, 'change' для select/checkbox
            if (el && (el.tagName === 'SELECT' || el.type === 'checkbox')) {
                 el.addEventListener('change', applyFilters);
            }
        });

        // Для модальных окон регистрации операций, нужно чтобы select'ы товаров были заполнены
        // Это уже делается в fetchAndRenderProducts -> loadProductsForOperationForms
        // Убедимся, что модальные окна Bootstrap корректно работают с динамическим контентом, если он там есть
        // (в нашем случае, формы статичны, а списки в select-ах обновляются)
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ЖУРНАЛА ОПЕРАЦИЙ (operations_log.html) ---
    if (currentPath.includes('/operations_log') || currentPath.includes('/operations') && !currentPath.includes('/api')) { // Учитываем /operations для Flask маршрута
        const operationsTableBody = document.querySelector('#operationsTableBody'); // Добавьте id="operationsTableBody" к tbody
        const filterForm = document.querySelector('#operationsFilterForm'); // Добавьте id форме фильтров

        function renderOperations(operations) {
            if (!operationsTableBody) return;
            operationsTableBody.innerHTML = '';
             if (!operations || operations.length === 0) {
                operationsTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Операции не найдены.</td></tr>';
                return;
            }
            operations.forEach(op => {
                const row = operationsTableBody.insertRow();
                row.innerHTML = `
                    <td>${new Date(op.date).toLocaleString('ru-RU')}</td>
                    <td><span class="badge bg-${op.type === 'Поступление' ? 'success' : 'warning text-dark'}">${op.type}</span></td>
                    <td>${op.product_name}</td>
                    <td>${op.quantity}</td>
                    <td>${op.invoice_number || '-'}</td>
                    <td>${op.party || '-'}</td>
                    <td>${op.comment || '-'}</td>
                `;
            });
        }

        async function fetchAndRenderOperations(params = {}) {
            const queryParams = new URLSearchParams(params).toString();
            const operations = await fetchData(`${apiBaseUrl}/operations${queryParams ? '?' + queryParams : ''}`);
            if (operations) {
                renderOperations(operations);
            }
        }

        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(filterForm);
                const params = {
                    start_date: formData.get('startDate'),
                    end_date: formData.get('endDate'),
                    operation_type: formData.get('operationType')
                };
                // Удаляем пустые параметры, чтобы не засорять URL
                for (const key in params) {
                    if (!params[key]) {
                        delete params[key];
                    }
                }
                fetchAndRenderOperations(params); // На бэкенде пока нет фильтрации по этим параметрам
            });
        }
        fetchAndRenderOperations(); // Первоначальная загрузка
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ОТЧЕТОВ (reports.html) ---
    if (currentPath.includes('/reports')) {
        const reportForm = document.getElementById('reportForm');
        const reportTypeSelect = document.getElementById('reportType');
        const conditionalInputsContainer = document.getElementById('conditionalInputsContainer');
        const reportResultsArea = document.getElementById('reportResultsArea');
        const exportButtonsContainer = document.getElementById('exportButtons');

        let currentReportData = null; // Для экспорта

        // Функция для динамического добавления полей в зависимости от типа отчета
        // (уже есть в HTML, но продублируем/уточним логику в JS для полноты)
        async function updateConditionalInputs() {
            conditionalInputsContainer.innerHTML = '';
            const selectedType = reportTypeSelect.value;
            let productOptionsHtml = '';

            if (selectedType === 'product_movement_period') {
                const products = await fetchData(`${apiBaseUrl}/products`);
                if (products) {
                     products.forEach(p => productOptionsHtml += `<option value="${p.id}">${p.name}</option>`);
                }
            }

            if (selectedType === 'operations_period' || selectedType === 'product_movement_period') {
                conditionalInputsContainer.innerHTML = `
                    <div class="mb-3">
                        <label for="reportStartDate" class="form-label">Период с:</label>
                        <input type="date" class="form-control form-control-sm" id="reportStartDate" name="start_date" required>
                    </div>
                    <div class="mb-3">
                        <label for="reportEndDate" class="form-label">Период по:</label>
                        <input type="date" class="form-control form-control-sm" id="reportEndDate" name="end_date" required>
                    </div>
                `;
            }
            if (selectedType === 'product_movement_period') {
                conditionalInputsContainer.innerHTML += `
                    <div class="mb-3">
                        <label for="reportProductSelect" class="form-label">Выберите товар:</label>
                        <select class="form-select form-select-sm" id="reportProductSelect" name="product_id" required>
                            <option selected disabled value="">Выберите товар...</option>
                            ${productOptionsHtml}
                        </select>
                    </div>
                `;
            }
        }

        if (reportTypeSelect) {
            reportTypeSelect.addEventListener('change', updateConditionalInputs);
            updateConditionalInputs(); // Первоначальный вызов для загрузки товаров, если выбран нужный тип
        }


        function renderReport(report) {
            reportResultsArea.innerHTML = '';
            exportButtonsContainer.style.display = 'none';
            currentReportData = null;

            if (!report || !report.data || report.data.length === 0) {
                reportResultsArea.innerHTML = `<p class="text-muted">Данные для отчета "${report.title || ''}" не найдены или отчет пуст.</p>`;
                return;
            }

            currentReportData = report.data; // Сохраняем для экспорта
            let tableHTML = `<h5 class="mb-3">${report.title}</h5>`;
            tableHTML += '<div class="table-responsive"><table class="table table-sm table-bordered table-striped">';
            // Заголовки
            tableHTML += '<thead><tr>';
            report.columns.forEach(col => tableHTML += `<th>${col}</th>`);
            tableHTML += '</tr></thead>';
            // Данные
            tableHTML += '<tbody>';
            report.data.forEach(row => {
                tableHTML += '<tr>';
                report.columns.forEach(col => tableHTML += `<td>${row[col] !== undefined && row[col] !== null ? row[col] : '-'}</td>`);
                tableHTML += '</tr>';
            });
            tableHTML += '</tbody></table></div>';
            reportResultsArea.innerHTML = tableHTML;
            exportButtonsContainer.style.display = 'block';
        }


        if (reportForm) {
            reportForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const reportType = reportTypeSelect.value;
                if (!reportType) {
                    alert('Пожалуйста, выберите тип отчета.');
                    return;
                }
                const formData = new FormData(reportForm);
                const params = new URLSearchParams();
                // Добавляем параметры из conditionalInputsContainer
                const conditionalInputs = conditionalInputsContainer.querySelectorAll('input, select');
                conditionalInputs.forEach(input => {
                    if (input.name && input.value) {
                        params.append(input.name, input.value);
                    }
                });

                const report = await fetchData(`${apiBaseUrl}/reports/${reportType}?${params.toString()}`);
                if(report) {
                    renderReport(report);
                } else {
                     reportResultsArea.innerHTML = `<p class="text-danger">Не удалось сформировать отчет.</p>`;
                     exportButtonsContainer.style.display = 'none';
                }
            });
        }

        // Экспорт (простая реализация CSV)
        const exportCsvButton = exportButtonsContainer ? exportButtonsContainer.querySelector('.btn-success') : null;
        if (exportCsvButton) {
            exportCsvButton.addEventListener('click', () => {
                if (!currentReportData || currentReportData.length === 0) {
                    alert("Нет данных для экспорта.");
                    return;
                }
                const reportTitle = reportResultsArea.querySelector('h5') ? reportResultsArea.querySelector('h5').textContent : "report";
                const columns = Object.keys(currentReportData[0]);
                let csvContent = "data:text/csv;charset=utf-8," + columns.join(";") + "\n";

                currentReportData.forEach(row => {
                    const values = columns.map(col => {
                        let cellValue = row[col] !== undefined && row[col] !== null ? String(row[col]) : "";
                        cellValue = cellValue.replace(/"/g, '""'); // Экранирование кавычек
                        if (cellValue.includes(';') || cellValue.includes('\n') || cellValue.includes(',')) {
                            cellValue = `"${cellValue}"`; // Оборачиваем в кавычки, если есть разделители
                        }
                        return cellValue;
                    });
                    csvContent += values.join(";") + "\n";
                });

                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                link.setAttribute("download", `${reportTitle.replace(/\s+/g, '_')}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast("Отчет экспортирован в CSV");
            });
        }
         // Кнопка PDF (заглушка, т.к. генерация PDF на клиенте сложнее)
        const exportPdfButton = exportButtonsContainer ? exportButtonsContainer.querySelector('.btn-danger') : null;
        if (exportPdfButton) {
            exportPdfButton.addEventListener('click', () => {
                alert("Экспорт в PDF пока не реализован. Используйте печать страницы в PDF (Ctrl+P) или специализированные библиотеки.");
                // Для реальной генерации PDF можно использовать jsPDF, html2pdf.js
            });
        }

    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ УПРАВЛЕНИЯ КАТЕГОРИЯМИ (categories.html) ---
    if (currentPath.includes('/categories-management')) { // Соответствует Flask маршруту
        const categoriesListElement = document.getElementById('categoriesList'); // Нужен id="categoriesList" для ul/div списка
        const addCategoryForm = document.getElementById('addCategoryForm');
        const editCategoryForm = document.getElementById('editCategoryForm'); // В модальном окне
        const editCategoryModalElement = document.getElementById('editCategoryModal');
        const deleteCategoryModalElement = document.getElementById('deleteCategoryModal');
        const deleteCategoryConfirmButton = deleteCategoryModalElement ? deleteCategoryModalElement.querySelector('.btn-danger') : null;

        let currentCategoryIdToEdit = null;
        let currentCategoryIdToDelete = null;

        function renderCategories(categories) {
            if (!categoriesListElement) { // Предполагаем, что это <ul class="list-group">
                 console.error("Элемент #categoriesList не найден");
                 return;
            }
            categoriesListElement.innerHTML = '';
            if (!categories || categories.length === 0) {
                categoriesListElement.innerHTML = '<li class="list-group-item">Категории не найдены.</li>';
                return;
            }
            categories.forEach(cat => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.dataset.categoryId = cat.id;
                li.innerHTML = `
                    ${cat.name}
                    <span class="action-icons">
                        <a href="#" class="edit-category" data-bs-toggle="modal" data-bs-target="#editCategoryModal" title="Редактировать"><i class="bi bi-pencil-square"></i></a>
                        <a href="#" class="delete-category" data-bs-toggle="modal" data-bs-target="#deleteCategoryModal" title="Удалить"><i class="bi bi-trash3-fill"></i></a>
                    </span>
                `;
                categoriesListElement.appendChild(li);
            });
        }

        async function fetchAndRenderCategories() {
            const categories = await fetchData(`${apiBaseUrl}/categories`);
            if (categories) {
                renderCategories(categories);
            }
        }

        if (addCategoryForm) {
            addCategoryForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const categoryName = document.getElementById('newCategoryName').value;
                if (!categoryName.trim()) {
                    alert("Название категории не может быть пустым.");
                    return;
                }
                const result = await fetchData(`${apiBaseUrl}/categories`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: categoryName })
                });
                if (result && result.id) {
                    showToast('Категория успешно добавлена!');
                    fetchAndRenderCategories();
                    addCategoryForm.reset();
                } else {
                    showToast(result ? result.error : 'Ошибка при добавлении категории.', 'danger');
                }
            });
        }

        document.addEventListener('click', async (e) => {
            const editLink = e.target.closest('.edit-category');
            const deleteLink = e.target.closest('.delete-category');

            if (editLink) {
                e.preventDefault();
                const listItem = editLink.closest('li');
                currentCategoryIdToEdit = parseInt(listItem.dataset.categoryId);
                const categoryName = listItem.firstChild.textContent.trim(); // Получаем текст категории
                if (editCategoryForm) {
                     editCategoryForm.elements['editCategoryName'].value = categoryName;
                }
            }

            if (deleteLink) {
                e.preventDefault();
                 const listItem = deleteLink.closest('li');
                currentCategoryIdToDelete = parseInt(listItem.dataset.categoryId);
                const categoryName = listItem.firstChild.textContent.trim();
                 if (deleteCategoryModalElement) {
                    deleteCategoryModalElement.querySelector('#categoryNameToDelete').textContent = categoryName;
                }
            }
        });

        if (editCategoryForm && editCategoryModalElement) {
            editCategoryForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (currentCategoryIdToEdit === null) return;
                const newName = editCategoryForm.elements['editCategoryName'].value;
                 if (!newName.trim()) {
                    alert("Название категории не может быть пустым.");
                    return;
                }
                const result = await fetchData(`${apiBaseUrl}/categories/${currentCategoryIdToEdit}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName })
                });
                if (result && result.id) {
                    showToast('Категория успешно обновлена!');
                    fetchAndRenderCategories();
                    const modal = bootstrap.Modal.getInstance(editCategoryModalElement);
                    modal.hide();
                } else {
                    showToast(result ? result.error : 'Ошибка при обновлении категории.', 'danger');
                }
            });
        }

        if (deleteCategoryConfirmButton) {
            deleteCategoryConfirmButton.addEventListener('click', async () => {
                if (currentCategoryIdToDelete === null) return;
                const result = await fetchData(`${apiBaseUrl}/categories/${currentCategoryIdToDelete}`, {
                    method: 'DELETE'
                });
                 if (result && (result.message || response.status === 204)) {
                    showToast(result.message || 'Категория успешно удалена!');
                    fetchAndRenderCategories();
                    const modal = bootstrap.Modal.getInstance(deleteCategoryModalElement);
                    modal.hide();
                    currentCategoryIdToDelete = null;
                } else {
                    showToast(result ? result.error : 'Ошибка при удалении категории.', 'danger');
                }
            });
        }

        fetchAndRenderCategories(); // Первоначальная загрузка
    }

});
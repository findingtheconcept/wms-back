document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    const apiBaseUrl = '/api';
    let allProductsCache = []; // Кэш для товаров на странице продуктов
    let allCategoriesCache = []; // Кэш для категорий

    // --- ОБЩИЕ ФУНКЦИИ ---

    async function fetchData(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (response.status === 204) return { success: true, status: 204, message: "Действие выполнено успешно (нет содержимого)." };

            const responseData = await response.json().catch(() => {
                if (response.ok) return { success: false, error: `Неожиданный ответ от сервера (статус ${response.status}).`, status: response.status };
                return { success: false, error: `Ошибка HTTP: ${response.status}. Не удалось получить детали ошибки.`, status: response.status };
            });

            if (!response.ok) {
                console.error('Ошибка API:', responseData.error || `Ошибка HTTP: ${response.status}`);
                showToast(`Ошибка: ${responseData.error || response.statusText || 'Неизвестная ошибка'}`, 'danger');
                return { success: false, error: responseData.error || `Ошибка HTTP: ${response.status}`, status: response.status, data: responseData };
            }
            return { success: true, status: response.status, data: responseData };
        } catch (error) {
            console.error('Сетевая ошибка или ошибка парсинга JSON:', error);
            showToast('Произошла сетевая ошибка. Пожалуйста, проверьте ваше соединение или обратитесь к администратору.', 'danger');
            return { success: false, error: 'Сетевая ошибка или ошибка парсинга JSON.', status: 0 };
        }
    }


    function populateSelect(selectElement, items, valueField, textField, placeholder, defaultSelectedValue = "") {
        if (!selectElement) return;
        const currentValue = selectElement.value;
        selectElement.innerHTML = '';

        if (placeholder) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = "";
            placeholderOption.textContent = placeholder;
            placeholderOption.disabled = true;
            selectElement.appendChild(placeholderOption);
        }

        items.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueField];
            option.textContent = item[textField];
            selectElement.appendChild(option);
        });


        if (defaultSelectedValue !== "" && selectElement.querySelector(`option[value="${defaultSelectedValue}"]`)) {
            selectElement.value = defaultSelectedValue;
        } else if (currentValue && selectElement.querySelector(`option[value="${currentValue}"]`)) {
            selectElement.value = currentValue;
        } else if (placeholder) {
            selectElement.value = ""; 
        }
    }


    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();
        const toastId = 'toast-' + Date.now();
        const toastBgClass = type === 'success' ? 'bg-success' : (type === 'danger' ? 'bg-danger' : 'bg-primary');

        const toastHTML = `
            <div class="toast align-items-center text-white ${toastBgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}" data-bs-delay="5000">
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
        if (toastElement) {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
            toastElement.addEventListener('hidden.bs.toast', () => toastElement.remove());
        }
    }

    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        return container;
    }

    function formatDateForDateTimeLocal(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        // Проверка на валидность даты
        if (isNaN(date.getTime())) return '';

        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ВХОДА (login.html) ---

    // --- ОБЩАЯ ЗАГРУЗКА КАТЕГОРИЙ ---
    async function loadAndCacheCategories() {
        if (allCategoriesCache.length === 0) {
            const result = await fetchData(`${apiBaseUrl}/categories`);
            if (result.success && Array.isArray(result.data)) {
                allCategoriesCache = result.data;
            } else {
                showToast(result.error || 'Не удалось загрузить категории.', 'danger');
                allCategoriesCache = []; // Убедимся, что это массив
            }
        }
        return allCategoriesCache;
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ СПИСКА ТОВАРОВ (index.html) ---
    if (currentPath.includes('/products') || currentPath === '/') {
        const productTableBody = document.getElementById('productTableBody');
        const addProductForm = document.getElementById('addProductForm');
        const editProductForm = document.getElementById('editProductForm');
        const deleteProductModalElement = document.getElementById('deleteProductModal');
        const deleteProductConfirmButton = document.getElementById('confirmDeleteProduct');
        let currentProductIdToDelete = null;
        let currentProductToEditId = null;

        const addProductCategorySelect = document.getElementById('addProductCategory');
        const editProductCategorySelect = document.getElementById('editProductCategory');
        const filterCategorySelect = document.getElementById('filterCategory');

        const registerIncomingForm = document.getElementById('registerIncomingForm');
        const registerOutgoingForm = document.getElementById('registerOutgoingForm');
        const incomingProductSelect = document.getElementById('incomingProduct');
        const outgoingProductSelect = document.getElementById('outgoingProduct');

        async function loadCategoriesForProductForms() {
            const categories = await loadAndCacheCategories();
            populateSelect(addProductCategorySelect, categories, 'id', 'name', 'Выберите категорию...');
            populateSelect(editProductCategorySelect, categories, 'id', 'name', 'Выберите категорию...'); 
            const filterCategories = [{ id: "", name: "Все категории" }, ...categories];
            populateSelect(filterCategorySelect, filterCategories, 'id', 'name', ''); 
            filterCategorySelect.value = "";
        }

        function populateProductSelectsForOperations(products) {
            populateSelect(incomingProductSelect, products, 'id', 'name', 'Выберите товар...');
            populateSelect(outgoingProductSelect, products, 'id', 'name', 'Выберите товар...');
        }

        function renderProducts(productsToRender) {
            if (!productTableBody) return;
            productTableBody.innerHTML = '';
            if (!productsToRender || productsToRender.length === 0) {
                productTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Товары не найдены.</td></tr>';
                return;
            }
            productsToRender.forEach(product => {
                const row = productTableBody.insertRow();
                row.dataset.productId = product.id;
                row.innerHTML = `
                    <td>${product.name || 'N/A'}</td>
                    <td>${product.category_name || 'N/A'}</td>
                    <td>${product.unit || 'N/A'}</td>
                    <td>${product.location || '-'}</td>
                    <td>${product.min_stock !== undefined ? product.min_stock : 'N/A'}</td>
                    <td>${product.current_stock !== undefined ? product.current_stock : 'N/A'} ${product.current_stock < product.min_stock ? '<i class="bi bi-exclamation-triangle-fill text-danger ms-1" title="Остаток ниже минимума"></i>' : ''}</td>
                    <td class="action-icons">
                        <a href="#" class="edit-product" title="Редактировать" data-bs-toggle="modal" data-bs-target="#editProductModal" data-product-id="${product.id}"><i class="bi bi-pencil-square"></i></a>
                        <a href="#" class="delete-product" title="Удалить" data-bs-toggle="modal" data-bs-target="#deleteProductModal" data-product-id="${product.id}" data-product-name="${product.name}"><i class="bi bi-trash3-fill"></i></a>
                    </td>
                `;
            });
        }

        async function fetchAndRenderProducts() {
            const result = await fetchData(`${apiBaseUrl}/products`);
            if (result.success && Array.isArray(result.data)) {
                allProductsCache = result.data; 
                applyFilters(); 
                populateProductSelectsForOperations(allProductsCache);
            } else {
                showToast(result.error || 'Не удалось загрузить товары.', 'danger');
                allProductsCache = [];
                renderProducts([]); 
            }
        }

        if (addProductForm) {
            addProductForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(addProductForm);
                const productData = {
                    name: formData.get('name'),
                    category_id: parseInt(formData.get('category_id')),
                    unit: formData.get('unit'),
                    description: formData.get('description'),
                    location: formData.get('location'),
                    min_stock: parseInt(formData.get('min_stock')),
                    // current_stock по умолчанию 0 на бэкенде
                };

                const result = await fetchData(`${apiBaseUrl}/products`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(productData)
                });

                if (result.success && result.data && result.data.id) {
                    showToast('Товар успешно добавлен!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
                    modal.hide();
                    addProductForm.reset();
                    if (addProductCategorySelect.options.length > 0 && addProductCategorySelect.options[0].value === "") {
                         addProductCategorySelect.selectedIndex = 0;
                    }
                } else {
                    showToast(result.error || 'Ошибка при добавлении товара.', 'danger');
                }
            });
        }

        productTableBody.addEventListener('click', async (e) => {
            const editButton = e.target.closest('.edit-product');
            if (editButton) {
                e.preventDefault();
                currentProductToEditId = parseInt(editButton.dataset.productId);
                const productToEdit = allProductsCache.find(p => p.id === currentProductToEditId);

                if (productToEdit && editProductForm) {
                    document.getElementById('editingProductName').textContent = productToEdit.name;
                    editProductForm.elements['name'].value = productToEdit.name;
                    populateSelect(editProductCategorySelect, allCategoriesCache, 'id', 'name', 'Выберите категорию...', productToEdit.category_id);
                    editProductForm.elements['unit'].value = productToEdit.unit;
                    editProductForm.elements['description'].value = productToEdit.description || '';
                    editProductForm.elements['location'].value = productToEdit.location || '';
                    editProductForm.elements['min_stock'].value = productToEdit.min_stock;
                } else if (!productToEdit) {
                     showToast('Не удалось найти данные товара для редактирования.', 'danger');
                }
            }

            const deleteButton = e.target.closest('.delete-product');
            if (deleteButton) {
                e.preventDefault();
                currentProductIdToDelete = parseInt(deleteButton.dataset.productId);
                const productName = deleteButton.dataset.productName;
                if (deleteProductModalElement) {
                    deleteProductModalElement.querySelector('#productNameToDelete').textContent = productName;
                }
            }
        });

        if (editProductForm) {
            editProductForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (currentProductToEditId === null) return;

                const formData = new FormData(editProductForm);
                const updatedData = {
                    name: formData.get('name'),
                    category_id: parseInt(formData.get('category_id')),
                    unit: formData.get('unit'),
                    description: formData.get('description'),
                    location: formData.get('location'),
                    min_stock: parseInt(formData.get('min_stock')),
                };

                const result = await fetchData(`${apiBaseUrl}/products/${currentProductToEditId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                });

                if (result.success && result.data && result.data.id) {
                    showToast('Товар успешно обновлен!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editProductModal'));
                    modal.hide();
                    currentProductToEditId = null;
                } else {
                     showToast(result.error || 'Ошибка при обновлении товара.', 'danger');
                }
            });
        }

        if (deleteProductConfirmButton) {
            deleteProductConfirmButton.addEventListener('click', async () => {
                if (currentProductIdToDelete === null) return;
                const result = await fetchData(`${apiBaseUrl}/products/${currentProductIdToDelete}`, {
                    method: 'DELETE'
                });

                if (result.success) { 
                    showToast(result.data?.message || result.message || 'Товар успешно удален!');
                    fetchAndRenderProducts();
                    const modal = bootstrap.Modal.getInstance(deleteProductModalElement);
                    modal.hide();
                    currentProductIdToDelete = null;
                } else {
                    showToast(result.error || 'Ошибка при удалении товара.', 'danger');
                }
            });
        }


        async function registerOperation(formElement, operationType) {
            const formData = new FormData(formElement);
            const operationData = {
                type: operationType,
                product_id: parseInt(formData.get('product_id')),
                quantity: parseInt(formData.get('quantity')),
                date: formData.get('date') || null, // null если пусто, бэкэнд поставит текущую
                invoice_number: formData.get('invoice_number'),
                party: formData.get(operationType === "Поступление" ? 'supplier' : 'recipient'),
                comment: formData.get('comment')
            };

             if (isNaN(operationData.product_id) || operationData.product_id <= 0) {
                showToast('Пожалуйста, выберите товар.', 'danger');
                return;
            }
            if (isNaN(operationData.quantity) || operationData.quantity <= 0) {
                showToast('Количество должно быть положительным числом.', 'danger');
                return;
            }

            const result = await fetchData(`${apiBaseUrl}/operations/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(operationData)
            });

            if (result.success && result.data && result.data.id) {
                showToast(`${operationType} успешно зарегистрировано!`);
                fetchAndRenderProducts(); // Обновить остатки в таблице товаров
                if (window.location.pathname.includes('/operations')) { 
                    fetchAndRenderOperations();
                }
                const modalId = operationType === "Поступление" ? 'registerIncomingModal' : 'registerOutgoingModal';
                const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
                modal.hide();
                formElement.reset();
                const productSelect = formElement.querySelector('select[name="product_id"]');
                if (productSelect && productSelect.options.length > 0 && productSelect.options[0].value === "") {
                    productSelect.selectedIndex = 0;
                }

            } else {
                showToast(result.error || `Ошибка регистрации ${operationType === "Поступление" ? "поступления" : "отгрузки"}.`, 'danger');
            }
        }

        if (registerIncomingForm) {
            registerIncomingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                registerOperation(registerIncomingForm, "Поступление");
            });
        }

        if (registerOutgoingForm) {
            registerOutgoingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                registerOperation(registerOutgoingForm, "Отгрузка");
            });
        }

        const searchNameInput = document.getElementById('searchName');
        const filterLocationInput = document.getElementById('filterLocation');
        const filterAvailabilitySelect = document.getElementById('filterAvailability');
        const filterMinStockCheckbox = document.getElementById('filterMinStock');

        function applyFilters() {
            const searchTerm = searchNameInput.value.toLowerCase();
            const categoryFilterId = filterCategorySelect.value; // Это ID
            const locationFilter = filterLocationInput.value.toLowerCase();
            const availabilityFilter = filterAvailabilitySelect.value;
            const minStockFilter = filterMinStockCheckbox.checked;

            let filteredProducts = [...allProductsCache]; 

            if (searchTerm) {
                filteredProducts = filteredProducts.filter(p => p.name.toLowerCase().includes(searchTerm));
            }
            if (categoryFilterId) { 
                filteredProducts = filteredProducts.filter(p => p.category_id == categoryFilterId);
            }
            if (locationFilter) {
                filteredProducts = filteredProducts.filter(p => p.location && p.location.toLowerCase().includes(locationFilter));
            }
            if (availabilityFilter === "in_stock") {
                filteredProducts = filteredProducts.filter(p => p.current_stock > 0);
            } else if (availabilityFilter === "out_of_stock") {
                filteredProducts = filteredProducts.filter(p => p.current_stock == 0); 
            }
            if (minStockFilter) {
                filteredProducts = filteredProducts.filter(p => p.current_stock < p.min_stock);
            }
            renderProducts(filteredProducts);
        }
        
        [searchNameInput, filterLocationInput].forEach(el => {
            if (el) el.addEventListener('input', applyFilters);
        });
        [filterCategorySelect, filterAvailabilitySelect, filterMinStockCheckbox].forEach(el => {
            if (el) el.addEventListener('change', applyFilters);
        });


        async function initProductPage() {
            await loadCategoriesForProductForms();
            await fetchAndRenderProducts();
        }
        initProductPage();
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ЖУРНАЛА ОПЕРАЦИЙ (operations_log.html) ---
    if (currentPath.includes('/operations') && !currentPath.includes('/api')) {
        const operationsTableBody = document.getElementById('operationsTableBody');
        const filterForm = document.getElementById('operationsFilterForm');

        function renderOperations(operations) {
            if (!operationsTableBody) return;
            operationsTableBody.innerHTML = '';
             if (!operations || operations.length === 0) {
                operationsTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Операции не найдены.</td></tr>';
                return;
            }
            operations.forEach(op => {
                const row = operationsTableBody.insertRow();
                let displayDate = 'N/A';
                if (op.date) {
                    try {
                        displayDate = new Date(op.date).toLocaleString('ru-RU', {
                            year: 'numeric', month: '2-digit', day: '2-digit',
                            hour: '2-digit', minute: '2-digit'
                        });
                    } catch (e) { console.error("Error parsing operation date:", op.date, e); }
                }

                row.innerHTML = `
                    <td>${displayDate}</td>
                    <td><span class="badge ${op.type === 'Поступление' ? 'bg-success' : 'bg-warning text-dark'}">${op.type || 'N/A'}</span></td>
                    <td>${op.product_name || 'N/A'}</td>
                    <td>${op.quantity !== undefined ? op.quantity : 'N/A'}</td>
                    <td>${op.invoice_number || '-'}</td>
                    <td>${op.party || '-'}</td>
                    <td>${op.comment || '-'}</td>
                `;
            });
        }

        async function fetchAndRenderOperations(params = {}) {
            const queryParams = new URLSearchParams();
            if (params.startDate) queryParams.append('start_date', params.startDate);
            if (params.endDate) queryParams.append('end_date', params.endDate);
            if (params.operationType && params.operationType !== "all") queryParams.append('type', params.operationType);

            const result = await fetchData(`${apiBaseUrl}/operations`);
            
            if (result.success && Array.isArray(result.data)) {
                let operationsToRender = result.data;
                if (params.startDate) {
                    operationsToRender = operationsToRender.filter(op => new Date(op.date) >= new Date(params.startDate));
                }
                if (params.endDate) {
                     operationsToRender = operationsToRender.filter(op => new Date(op.date) <= new Date(new Date(params.endDate).setHours(23,59,59,999))); // Включая конец дня
                }
                if (params.operationType && params.operationType !== "all") {
                    operationsToRender = operationsToRender.filter(op => op.type === params.operationType);
                }
                renderOperations(operationsToRender);
            } else {
                showToast(result.error || 'Не удалось загрузить операции.', 'danger');
                renderOperations([]);
            }
        }

        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const formData = new FormData(filterForm);
                const params = {
                    startDate: formData.get('startDate'),
                    endDate: formData.get('endDate'),
                    operationType: formData.get('operationType')
                };
                fetchAndRenderOperations(params);
            });
            const today = new Date().toISOString().split('T')[0];
            const startDateInput = document.getElementById('startDate');
            const endDateInput = document.getElementById('endDate');
            if(startDateInput && !startDateInput.value) startDateInput.value = today; // Если пусто, ставим сегодня
            if(endDateInput && !endDateInput.value) endDateInput.value = today;
        }
        fetchAndRenderOperations(); // Первоначальная загрузка
    }
    const showClearLogModalButton = document.getElementById('showClearLogModalButton');
    const clearLogConfirmationModalElement = document.getElementById('clearLogConfirmationModal');
    const confirmClearLogButton = document.getElementById('confirmClearLogButton');
    const clearLogConfirmationInput = document.getElementById('clearLogConfirmationInput');
    const clearLogError = document.getElementById('clearLogError');
    let clearLogModalInstance = null;

    if (clearLogConfirmationModalElement) {
        clearLogModalInstance = new bootstrap.Modal(clearLogConfirmationModalElement);
    }

    if (showClearLogModalButton && clearLogModalInstance) {
        showClearLogModalButton.addEventListener('click', () => {
            clearLogConfirmationInput.value = ''; // Сброс поля ввода
            clearLogError.textContent = ''; // Сброс сообщения об ошибке
            clearLogModalInstance.show();
        });
    }

    if (confirmClearLogButton && clearLogConfirmationInput) {
        confirmClearLogButton.addEventListener('click', async () => {
            if (clearLogConfirmationInput.value !== "УДАЛИТЬ") {
                clearLogError.textContent = 'Введено неверное слово для подтверждения.';
                return;
            }
            clearLogError.textContent = ''; 

            const result = await fetchData(`${apiBaseUrl}/operations/clear`, {
                method: 'DELETE'
            });

            if (result.success) {
                showToast(result.data?.message || result.message || 'Журнал операций успешно очищен!', 'success');
                fetchAndRenderOperations();
            } else {
                showToast(result.error || 'Ошибка при очистке журнала.', 'danger');
            }
            clearLogModalInstance.hide();
        });
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ ОТЧЕТОВ (reports.html) ---
    if (currentPath.includes('/reports')) {
        const reportForm = document.getElementById('reportForm');
        const reportTypeSelect = document.getElementById('reportType');
        const conditionalInputsContainer = document.getElementById('conditionalInputsContainer');
        const reportResultsArea = document.getElementById('reportResultsArea');
        const exportButtonsContainer = document.getElementById('exportButtons');
        const exportCsvButton = document.getElementById('exportCsvButton');
        const exportPdfButton = document.getElementById('exportPdfButton'); 
        let currentReportResponse = null; 

        async function updateConditionalInputsForReports() {
            conditionalInputsContainer.innerHTML = '';
            const selectedType = reportTypeSelect.value;

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
                const productsResult = await fetchData(`${apiBaseUrl}/products`); 
                let productOptionsHtml = '';
                if (productsResult.success && Array.isArray(productsResult.data)) {
                     productsResult.data.forEach(p => productOptionsHtml += `<option value="${p.id}">${p.name}</option>`);
                }
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
            reportTypeSelect.addEventListener('change', updateConditionalInputsForReports);
            updateConditionalInputsForReports(); 
        }

        function renderReport(reportResponse) { 
            reportResultsArea.innerHTML = '';
            exportButtonsContainer.style.display = 'none';
            currentReportResponse = null;

            if (!reportResponse || !reportResponse.data) {
                reportResultsArea.innerHTML = `<p class="text-muted">Ошибка при загрузке отчета или отчет пуст.</p>`;
                showToast(reportResponse?.message || 'Данные для отчета не найдены.', 'warning');
                return;
            }
            
            if (reportResponse.data.length === 0) {
                reportResultsArea.innerHTML = `<h5 class="mb-3">${reportResponse.title || 'Отчет'}</h5> <p class="text-muted">Данные для этого отчета отсутствуют.</p>`;
                return;
            }


            currentReportResponse = reportResponse; 
            let tableHTML = `<h5 class="mb-3">${reportResponse.title}</h5>`;
            tableHTML += '<div class="table-responsive"><table class="table table-sm table-bordered table-striped">';
            
            tableHTML += '<thead><tr>';
            reportResponse.columns.forEach(col => tableHTML += `<th>${col}</th>`);
            tableHTML += '</tr></thead>';
            
            tableHTML += '<tbody>';
            reportResponse.data.forEach(row => {
                tableHTML += '<tr>';
                reportResponse.columns.forEach(col => {
                    let cellValue = row[col];
                    if (typeof col === 'string' && col.toLowerCase() === 'дата' && typeof cellValue === 'string' && cellValue.includes('T')) {
                         try {
                            cellValue = new Date(cellValue).toLocaleString('ru-RU', {
                                year: 'numeric', month: '2-digit', day: '2-digit',
                                hour: '2-digit', minute: '2-digit'
                            });
                        } catch(e) { /* оставляем как есть, если не парсится */ }
                    }
                    tableHTML += `<td>${cellValue !== undefined && cellValue !== null ? cellValue : '-'}</td>`;
                });
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
                    showToast('Пожалуйста, выберите тип отчета.', 'warning');
                    return;
                }
                const params = new URLSearchParams();
                const conditionalInputs = conditionalInputsContainer.querySelectorAll('input, select');
                let allFieldsValid = true;
                conditionalInputs.forEach(input => {
                    if (input.required && !input.value) {
                        allFieldsValid = false;
                        input.classList.add('is-invalid'); // Bootstrap класс для подсветки
                    } else {
                        input.classList.remove('is-invalid');
                    }
                    if (input.name && input.value) {
                        params.append(input.name, input.value);
                    }
                });

                if (!allFieldsValid) {
                    showToast('Пожалуйста, заполните все обязательные поля для отчета.', 'danger');
                    return;
                }

                const result = await fetchData(`${apiBaseUrl}/reports/${reportType}?${params.toString()}`);
                if(result.success) {
                    renderReport(result.data);
                } else {
                     reportResultsArea.innerHTML = `<p class="text-danger">${result.error || 'Не удалось сформировать отчет.'}</p>`;
                     exportButtonsContainer.style.display = 'none';
                }
            });
        }

        if (exportCsvButton) {
            exportCsvButton.addEventListener('click', () => {
                if (!currentReportResponse || !currentReportResponse.data || currentReportResponse.data.length === 0) {
                    showToast("Нет данных для экспорта.", "warning");
                    return;
                }
                const { title, columns, data } = currentReportResponse;
                let csvContent = "data:text/csv;charset=utf-8,\uFEFF"; // \uFEFF for BOM UTF-8 Excel
                csvContent += columns.join(";") + "\n";

                data.forEach(row => {
                    const values = columns.map(col => {
                        let cellValue = row[col] !== undefined && row[col] !== null ? String(row[col]) : "";
                        if (typeof col === 'string' && col.toLowerCase() === 'дата' && typeof cellValue === 'string' && cellValue.includes('T')) {
                             try {
                                cellValue = new Date(cellValue).toLocaleString('ru-RU', {
                                    year: 'numeric', month: '2-digit', day: '2-digit',
                                    hour: '2-digit', minute: '2-digit'
                                });
                            } catch(e) { /* оставляем как есть */ }
                        }
                        cellValue = cellValue.replace(/"/g, '""'); 
                        if (cellValue.includes(';') || cellValue.includes('\n') || cellValue.includes(',')) {
                            cellValue = `"${cellValue}"`; 
                        }
                        return cellValue;
                    });
                    csvContent += values.join(";") + "\n";
                });

                const encodedUri = encodeURI(csvContent);
                const link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                const fileName = title ? title.replace(/[^a-zа-я0-9\s-]/gi, '').replace(/\s+/g, '_') : 'report';
                link.setAttribute("download", `${fileName}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast("Отчет экспортирован в CSV", "success");
            });
        }
        if (exportPdfButton) { 
            
            exportPdfButton.addEventListener('click', () => {
                if (!currentReportResponse || !currentReportResponse.data || currentReportResponse.data.length === 0) {
                    showToast("Нет данных для экспорта в PDF.", "warning");
                    return;
                }

                const reportType = reportTypeSelect.value;
                if (!reportType) {
                    showToast('Тип отчета не выбран для экспорта в PDF.', 'warning');
                    return;
                }

                const params = new URLSearchParams();
                const conditionalInputs = conditionalInputsContainer.querySelectorAll('input, select');
                let allFieldsValid = true;
                conditionalInputs.forEach(input => {
                    if (input.required && !input.value) {
                        allFieldsValid = false;
                    }
                    if (input.name && input.value) {
                        params.append(input.name, input.value);
                    }
                });

                if (!allFieldsValid && (reportType === 'operations_period' || reportType === 'product_movement_period')) {
                    showToast('Пожалуйста, заполните все обязательные поля для выбранного типа отчета перед экспортом в PDF.', 'danger');
                    return;
                }
                
                let pdfUrl = `${apiBaseUrl}/reports/${reportType}/pdf`;
                if (params.toString()) {
                    pdfUrl += `?${params.toString()}`;
                }

                window.open(pdfUrl, '_blank');
                showToast("Запрос на формирование PDF отправлен. Загрузка начнется автоматически.", "info");
            });
        }
    }


    // --- ЛОГИКА ДЛЯ СТРАНИЦЫ УПРАВЛЕНИЯ КАТЕГОРИЯМИ (categories.html) ---
    if (currentPath.includes('/categories-management')) {
        const categoriesListElement = document.getElementById('categoriesList');
        const addCategoryForm = document.getElementById('addCategoryForm');
        const editCategoryForm = document.getElementById('editCategoryForm');
        const editCategoryModalElement = document.getElementById('editCategoryModal');
        const deleteCategoryModalElement = document.getElementById('deleteCategoryModal');
        const deleteCategoryConfirmButton = document.getElementById('confirmDeleteCategory');

        let currentCategoryIdToEdit = null;
        let currentCategoryNameToEdit = '';
        let currentCategoryIdToDelete = null;


        function renderCategoriesList(categories) {
            if (!categoriesListElement) return;
            categoriesListElement.innerHTML = '';
            if (!categories || categories.length === 0) {
                categoriesListElement.innerHTML = '<li class="list-group-item text-center text-muted">Категории не найдены.</li>';
                return;
            }
            categories.forEach(cat => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';
                li.dataset.categoryId = cat.id;
                li.dataset.categoryName = cat.name;
                li.dataset.categoryDescription = cat.description || '';

                li.innerHTML = `
                    <div>
                        <strong>${cat.name}</strong>
                        ${cat.description ? `<br><small class="text-muted">${cat.description}</small>` : ''}
                    </div>
                    <span class="action-icons">
                        <a href="#" class="edit-category" data-bs-toggle="modal" data-bs-target="#editCategoryModal" title="Редактировать"><i class="bi bi-pencil-square"></i></a>
                        <a href="#" class="delete-category" data-bs-toggle="modal" data-bs-target="#deleteCategoryModal" title="Удалить"><i class="bi bi-trash3-fill"></i></a>
                    </span>
                `;
                categoriesListElement.appendChild(li);
            });
        }

        async function fetchAndRenderCategoriesPage() {
            const result = await fetchData(`${apiBaseUrl}/categories`);
            if (result.success && Array.isArray(result.data)) {
                allCategoriesCache = result.data;
                renderCategoriesList(result.data);
            } else {
                showToast(result.error || 'Не удалось загрузить категории.', 'danger');
                renderCategoriesList([]);
            }
        }

        if (addCategoryForm) {
            addCategoryForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const categoryNameInput = document.getElementById('newCategoryName');
                const categoryName = categoryNameInput.value.trim();

                if (!categoryName) {
                    showToast("Название категории не может быть пустым.", 'warning');
                    categoryNameInput.focus();
                    return;
                }
                const result = await fetchData(`${apiBaseUrl}/categories`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: categoryName /*, description: categoryDescription */})
                });

                if (result.success && result.data && result.data.id) {
                    showToast('Категория успешно добавлена!');
                    fetchAndRenderCategoriesPage();
                    addCategoryForm.reset();
                } else {
                    showToast(result.error || 'Ошибка при добавлении категории.', 'danger');
                }
            });
        }

        categoriesListElement.addEventListener('click', (e) => {
            const listItem = e.target.closest('li.list-group-item');
            if (!listItem) return;

            const editLink = e.target.closest('.edit-category');
            const deleteLink = e.target.closest('.delete-category');

            if (editLink) {
                e.preventDefault();
                currentCategoryIdToEdit = parseInt(listItem.dataset.categoryId);
                currentCategoryNameToEdit = listItem.dataset.categoryName;
                const currentCategoryDescription = listItem.dataset.categoryDescription;

                if (editCategoryForm) {
                     editCategoryForm.elements['editCategoryName'].value = currentCategoryNameToEdit;
 
                     document.getElementById('editingCategoryNamePlaceholder').textContent = currentCategoryNameToEdit; 
                }
            }

            if (deleteLink) {
                e.preventDefault();
                currentCategoryIdToDelete = parseInt(listItem.dataset.categoryId);
                const categoryName = listItem.dataset.categoryName;
                 if (deleteCategoryModalElement) {
                    deleteCategoryModalElement.querySelector('#categoryNameToDelete').textContent = categoryName;
                }
            }
        });

        if (editCategoryForm && editCategoryModalElement) {
            editCategoryForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                if (currentCategoryIdToEdit === null) return;

                const newNameInput = editCategoryForm.elements['editCategoryName'];
                const newName = newNameInput.value.trim();

                 if (!newName) {
                    showToast("Название категории не может быть пустым.", 'warning');
                    newNameInput.focus();
                    return;
                }
                const result = await fetchData(`${apiBaseUrl}/categories/${currentCategoryIdToEdit}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: newName /*, description: newDescription */ })
                });

                if (result.success && result.data && result.data.id) {
                    showToast('Категория успешно обновлена!');
                    fetchAndRenderCategoriesPage();
                    const modal = bootstrap.Modal.getInstance(editCategoryModalElement);
                    modal.hide();
                    currentCategoryIdToEdit = null;
                } else {
                    showToast(result.error || 'Ошибка при обновлении категории.', 'danger');
                }
            });
        }

        if (deleteCategoryConfirmButton) {
            deleteCategoryConfirmButton.addEventListener('click', async () => {
                if (currentCategoryIdToDelete === null) return;
                const result = await fetchData(`${apiBaseUrl}/categories/${currentCategoryIdToDelete}`, {
                    method: 'DELETE'
                });
                if (result.success) { // result.status === 200 || result.status === 204
                    showToast(result.data?.message || result.message || 'Категория успешно удалена!');
                    fetchAndRenderCategoriesPage(); 
                    const modal = bootstrap.Modal.getInstance(deleteCategoryModalElement);
                    modal.hide();
                    currentCategoryIdToDelete = null;
                } else {
                    showToast(result.error || 'Ошибка при удалении категории.', 'danger');
                }
            });
        }
        fetchAndRenderCategoriesPage();
    }
});
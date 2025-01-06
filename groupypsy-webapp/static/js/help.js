// Examples on Help page
function loadExampleTables() {
    fetch('/examples', {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || "Failed to load examples.");
                });
            }
            return response.json();
        })
        .then(data => {

            // Populate each table
            populateTable('studentsTable', data.data.students, data.column_order.students);
            populateTable('projectsTable', data.data.projects, data.column_order.projects);
            populateTable('requirementsTable', data.data.requirements, data.column_order.requirements);
            populateTable('choicesTable', data.data.choices, data.column_order.choices);
        })
        .catch(error => {
            console.error("Error loading examples:", error);
        });
}

function populateTable(tableId, data, columnOrder) {
    if (!data || data.length === 0 || !columnOrder) {
        console.error(`No data or column order available for table ${tableId}`);
        return;
    }

    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');

    // Clear existing content
    thead.innerHTML = "";
    tbody.innerHTML = "";

    // Populate headers using the column order
    const headerRow = document.createElement('tr');
    columnOrder.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    // Populate rows using the column order
    data.forEach(row => {
        const tr = document.createElement('tr');
        columnOrder.forEach(header => {
            const td = document.createElement('td');
            td.textContent = row[header];
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });

    // Initialize DataTables
    if ($.fn.DataTable.isDataTable(`#${tableId}`)) {
        $(`#${tableId}`).DataTable().clear().destroy();
    }
    $(`#${tableId}`).DataTable({
        paging: true,
        searching: true,
        ordering: true,
        info: true,
        responsive: true,
    });
}

// Call this function on page load
document.addEventListener('DOMContentLoaded', loadExampleTables);
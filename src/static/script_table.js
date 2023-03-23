const timeConv = {
    "days": 1,
    "weeks": 7,
    "months": 30,
    "years": 365,
    "N/A": -1
};

const itemColumns = ["ItemID", "ItemName", "ItemDescription", "ShelfLife", "Price", "AvailableStock", "Unit"];
const requestColumns = ["RequestID", "ItemID", "ItemName", "ItemDescription", "RequestedBy", "RequestQuantity", "Unit", "RequestDate", "Status"];
const deliveryColumns = ["DeliveryID", "ItemID", "ItemName", "ItemDescription", "DeliveryQuantity", "Unit", "ShelfLife", "DeliveryDate", "ReceivedBy", "IsExpired"];

function escapeKeyword (k) {
    return k.replaceAll(/[\u2018\u2019\u201c\u201d]/gu, x => (x === '\u2018' || x === '\u2019') ? '"' : "'").replaceAll(/[:/?#\[\]@!$&'()*+,;=%]/g, x => "%" + x.charCodeAt(0).toString(16).toUpperCase());
}

function getRequestItemsTable(contents = []){
    let table = document.createElement("div"), tm = document.createElement("div"), th = document.createElement("div"), tb = document.createElement("div"), tr = document.createElement("div");
    table.classList.add("table-wrapper");

    tm.classList.add("table-main");
    tm.classList.add("request-items-table");

    th.classList.add("table-header")
    th.innerHTML = `
    <div class="table-row">
        <div>Item Name</div>
        <div>Item Description</div>
        <div>Quantity</div>
    </div>
    `;
    tm.appendChild(th);

    tb.classList.add("table-body");

    for (let i = 0; i < contents.length; i++){
        let tr = document.createElement("div");
        tr.classList.add("table-row");
        for (let j = 0; j < contents[i].length; j++){
            let td = document.createElement("div");
            td.innerHTML = contents[i][j];
            tr.appendChild(td);
        }
        tb.appendChild(tr);
    }
    tm.appendChild(tb);
    table.appendChild(tm);

    return table
}

async function getItems (keyword = "") {
    return fetch(encodeURI(`/inventory/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["items"]);
}

async function populateItems (tbody, keyword = "", { stock = true, buttons = false, requesting = false } = {}) {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getItems(keyword);
    let rows = [];

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i of itemColumns) {
            if (!stock && i === 'AvailableStock') continue;

            let y = x[i];
            let td = document.createElement("div");
            
            if (i === "Price") {
                let t0 = document.createElement("div");
                t0.classList.add("currency");
                let [t1, t2] = [document.createElement("span"), document.createElement("span")];
                t1.innerHTML = y[0];
                t2.innerHTML = y.slice(1);
                t0.appendChild(t1);
                t0.appendChild(t2);
                td.appendChild(t0);
            } else td.innerHTML = y;

            if (i === "ItemID") td.classList.add("mono");
            if (i === "ItemDescription") td.classList.add("left");
            if (i === "Price") td.classList.add("tabnum");
            if (i === "AvailableStock" && y === "0") td.classList.add("red");

            tr.appendChild(td);
        }
        
        if (buttons) {
            let e = document.createElement("div");
            let b = document.createElement("button");
            b.type = "button";
            b.role = "button";
            b.innerHTML = "<i class='bi bi-plus-circle'></i><i class='bi bi-plus-circle-fill'></i>";
            b.classList.add("select-row");
            if (requesting && x['AvailableStock'] === "0") b.disabled = true;
            e.appendChild(b);
            tr.appendChild(e);
        }

        tbody.appendChild(tr);
        rows.push(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));

    return rows;
}

async function getRequests (keyword = "", requestStatus = "") {
    return fetch(encodeURI(`/requests/search?requestStatus=` + requestStatus + `${keyword === "" ? "" : "&keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["requests"]);
}

// Request Status inputs: all, user, Pending, Approved, Issued, Completed
async function populateRequests (tbody, keyword = "", requestStatus="") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let requests = await getRequests(keyword, requestStatus);

    for (let req of requests){
        let tr = document.createElement("div");
        tr.classList.add("table-row")
        tr.classList.add("request-details")

        for (let i = 0; i < 4; i++){
            let td = document.createElement("div");
            td.innerText = req[i];

            tr.appendChild(td);
        }
        tr.appendChild(getRequestItemsTable(req[4]));
        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (requests.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

async function getDeliveries (keyword = "") {
    return fetch(encodeURI(`/deliveries/search${keyword === "" ? "" : "?keywords=" + escapeKeyword(keyword)}`)).then(d => d.json()).then(j => j["deliveries"]);
}

async function populateDeliveries (tbody, keyword = "") {
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);

    tbody.querySelector(".table-loading").classList.remove("hide");
    tbody.querySelector(".table-empty").classList.add("hide");

    let items = await getDeliveries(keyword);

    for (let x of items) {
        let tr = document.createElement("div");
        tr.classList.add("table-row");

        for (let i of deliveryColumns) {
            let y = x[i];
            let td = document.createElement("div");

            if (i === 'IsExpired') {
                if (y) {
                    let span = document.createElement("span");
                    span.classList.add("status");
                    span.classList.add("expired");
                    span.innerText = "expired";
                    td.appendChild(span);
                }
            } else td.innerText = y;

            if (i === "ItemID") td.classList.add("mono");
            if (i === "ItemDescription") td.classList.add("left");

            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    }

    tbody.querySelector(".table-loading").classList.add("hide");
    if (items.length > 0) tbody.querySelector(".table-empty").classList.add("hide");
    else tbody.querySelector(".table-empty").classList.remove("hide");

    document.dispatchEvent(new CustomEvent("tablerefresh"));
}

function sortTable (table, column, currentSort, { shelfLife = false, numerical = false } = {}) {
    let oldSym = table.querySelector(`.table-header .table-row > :nth-child(${currentSort[0] + 1}) .bi`);
    oldSym.classList.remove(`bi-chevron-${currentSort[1] ? "up" : "down"}`);
    oldSym.classList.add("bi-chevron-expand");
    
    let tbody = table.querySelector(".table-body");

    let rows = Array.from(tbody.querySelectorAll(".table-row:not(.hide)"));
    currentSort = [column, column === currentSort[0] ? !currentSort[1] : true];
    rows.sort((a, b) => {
        let [x, y] = [a.children[column].innerText, b.children[column].innerText];
        let s;

        if (shelfLife) {
            s = (2 * +currentSort[1] - 1) * (+x - +y);
            if (Number.isNaN(s)) s = +(x === '\u2014') + -(y === '\u2014');
        } else if (numerical) s = (currentSort[1] ? 1 : -1) * (+x - +y);
        else s = (currentSort[1] ? 1 : -1) * x.localeCompare(y);

        return s === 0 ? a.children[0].innerText.localeCompare(b.children[0].innerText) : s;
    });
    while (tbody.childElementCount > 2) tbody.removeChild(tbody.lastChild);
    for (let row of rows) tbody.appendChild(row);
    
    let newSym = table.querySelector(`.table-header .table-row > :nth-child(${currentSort[0] + 1}) .bi`);
    newSym.classList.remove("bi-chevron-expand");
    newSym.classList.add(`bi-chevron-${currentSort[1] ? "up" : "down"}`);

    return currentSort;
}

document.addEventListener("DOMContentLoaded", function() {
    const awaitingBidsCheck = document.querySelector("#awaitingBidsCheck");
    const bidsReceivedCheck = document.querySelector("#bidsReceivedCheck");
    const completeCheck = document.querySelector("#completeCheck");

    awaitingBidsCheck.addEventListener("click", filterTable);
    bidsReceivedCheck.addEventListener("click", filterTable);
    completeCheck.addEventListener("click", filterTable);
});

const filterTable = () => {
    const awaitingBidsCheck = document.querySelector("#awaitingBidsCheck");
    const bidsReceivedCheck = document.querySelector("#bidsReceivedCheck");
    const completeCheck = document.querySelector("#completeCheck");

    const filters = [];
    if (awaitingBidsCheck.checked) {
        filters.push("Awaiting Bids");
    }
    if (bidsReceivedCheck.checked) {
        filters.push("Bid(s) Received");
    }
    if (completeCheck.checked) {
        filters.push("Complete");
    }

    const table = document.getElementById("requestsTable");
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {  // Start from 1 to skip the header row
        const td = tr[i].querySelector('td[name="Status"]');  // Select td with name="Status"
        if (td) {
            const txtValue = td.textContent || td.innerText;
            if (filters.length === 0 || filters.some(filter => txtValue.indexOf(filter) > -1)) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
};

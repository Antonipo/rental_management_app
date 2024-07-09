document.addEventListener('DOMContentLoaded', function() {
    var popup = document.getElementById("welcomePopup");
    var span = document.getElementsByClassName("close")[0];

    // Mostrar el popup al cargar la página
    popup.style.display = "block";

    // Cerrar el popup cuando se hace clic en (x)
    span.onclick = function() {
        popup.style.display = "none";
    }

    // Cerrar el popup si se hace clic fuera de él
    window.onclick = function(event) {
        if (event.target == popup) {
            popup.style.display = "none";
        }
    }
});
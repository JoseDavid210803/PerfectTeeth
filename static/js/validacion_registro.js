document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const semestreField = document.querySelector("#id_semestre");

    form.addEventListener("submit", function (event) {
        const semestre = parseInt(semestreField.value);

        if (isNaN(semestre) || semestre < 4) {
            event.preventDefault();
            alert("Solo se pueden registrar alumnos de 4º semestre en adelante.");
            return false;
        }
    });
});

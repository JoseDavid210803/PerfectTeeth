function mostrarSeccion(id) {
    const secciones = ['inicio','cita','historial','seguimiento','especialidad'];
    secciones.forEach(sec => {
      const el = document.getElementById('section-' + sec);
      if (el) el.classList.toggle('d-none', sec !== id);
    });
    document.querySelectorAll('.sidebar .nav-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.sidebar .nav-link').forEach(l => {
      if (l.getAttribute('onclick').includes(id)) l.classList.add('active');
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    mostrarSeccion('inicio');

    // Inicia Flatpickr
    const fechaPicker = flatpickr("#fechaCita", {
      dateFormat: "Y-m-d",
      minDate: "today",
      maxDate: new Date().fp_incr(30),
      disable: [
        function(date) {
          return (date.getDay() === 0 || date.getDay() === 6);
        }
      ],
      locale: {
        firstDayOfWeek: 1,
        weekdays: {
          shorthand: ['Do','Lu','Ma','Mi','Ju','Vi','Sa'],
          longhand: ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado']
        },
        months: {
          shorthand: ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'],
          longhand: ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
        }
      }
    });

    // Generar opciones de hora
    const horaSelect = document.getElementById("horaCita");
    if (horaSelect) {
      for (let h = 8; h < 20; h++) {
        ["00", "30"].forEach(m => {
          const time = `${String(h).padStart(2, '0')}:${m}`;
          const opt = document.createElement("option");
          opt.value = time;
          opt.textContent = time;
          horaSelect.appendChild(opt);
        });
      }
    }
  });
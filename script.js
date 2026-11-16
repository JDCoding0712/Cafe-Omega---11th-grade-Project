let products = [];
  const money=n=>'RD$ '+n.toLocaleString('es-DO');
  const key='bruma-cafe-cart-v1';let cart={};let activeCategory='Todos';
  try{const saved=JSON.parse(localStorage.getItem(key)||'{}');if(saved&&typeof saved==='object'&&!Array.isArray(saved)){cart=Object.fromEntries(Object.entries(saved).filter(([id,qty])=>products.some(p=>String(p.id)===id)&&Number.isInteger(qty)&&qty>0&&qty<=99));}}catch(e){cart={};}
  const $=id=>document.getElementById(id);const save=()=>{try{localStorage.setItem(key,JSON.stringify(cart));}catch(e){}};
  function renderFilters(){const categories=['Todos','Cafés','Bebidas','Comidas'];$('filters').innerHTML=categories.map(c=>`<button type="button" class="filter ${activeCategory===c?'active':''}" data-filter="${c}" aria-pressed="${activeCategory===c}">${c}</button>`).join('');}
  function renderProducts(){ $('products').innerHTML=products.filter(p=>activeCategory==='Todos'||p.category===activeCategory).map(p=>`<article class="product"><img src="${p.image}" alt="${p.name}" loading="lazy"><div class="product-info"><div class="category">${p.category}</div><h3>${p.name}</h3><p>${p.description}</p><div class="buy-row"><span class="price">${money(p.price)}</span><button type="button" class="add" data-add="${p.id}">+ Agregar</button></div></div></article>`).join('');}
  function renderCart(){let count=0,total=0;const rows=products.filter(p=>cart[p.id]).map(p=>{let q=cart[p.id];count+=q;total+=q*p.price;return `<div class="cart-line"><div class="item-head"><strong>${p.name}</strong><span>${money(q*p.price)}</span></div><div class="quantity"><span>${money(p.price)} c/u</span><div class="quantity-controls"><button type="button" aria-label="Quitar uno de ${p.name}" data-dec="${p.id}">−</button><strong>${q}</strong><button type="button" aria-label="Agregar uno de ${p.name}" data-add="${p.id}">+</button></div></div></div>`;});$('cartList').innerHTML=rows.length?rows.join(''):'<div class="empty">🛍️<br>Tu carrito está vacío.<br>¡Agrega algo delicioso!</div>';$('cartCount').textContent=count;$('total').textContent=money(total);$('checkout').disabled=!count;save();}
  document.addEventListener('click',event=>{const filter=event.target.closest('[data-filter]');if(filter){activeCategory=filter.dataset.filter;renderFilters();renderProducts();return;}const add=event.target.closest('[data-add]');if(add){const id=add.dataset.add;cart[id]=Math.min(99,(cart[id]||0)+1);$('notice').textContent='';renderCart();return;}const dec=event.target.closest('[data-dec]');if(dec){const id=dec.dataset.dec;cart[id]--;if(cart[id]<=0)delete cart[id];$('notice').textContent='';renderCart();}});
  
/* =========================================
   CONFIRMAR PEDIDOS REALES - CAFÉ-OMEGA
========================================= */

$('checkout').addEventListener('click', async () => {

    const aviso = $('notice');
    const boton = $('checkout');

    // Verificar que el cliente haya iniciado sesión
    const sesion = window.cafeOmegaSesion;

    if (!sesion || !sesion.token) {
        aviso.textContent =
            '🔐 Debes iniciar sesión para confirmar tu pedido.';

        mostrarFormulario('login');
        return;
    }

    // Obtener los productos del carrito
    const items = Object.entries(cart)
        .filter(([id, cantidad]) =>
            Number.isInteger(cantidad) &&
            cantidad > 0 &&
            cantidad <= 99
        )
        .map(([id, cantidad]) => ({
            producto_id: Number(id),
            cantidad: cantidad
        }));

    if (items.length === 0) {
        aviso.textContent = 'Tu carrito está vacío.';
        return;
    }

    // Evitar que el usuario envíe el pedido dos veces
    boton.disabled = true;
    aviso.textContent = '☕ Estamos registrando tu pedido...';

    try {
        const respuesta = await fetch('/pedidos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + sesion.token
            },
            body: JSON.stringify({ items })
        });

        const resultado = await respuesta.json();

        // Si la sesión expiró
        if (respuesta.status === 401) {
            window.cafeOmegaSesion = null;

            document.getElementById('loginNav').hidden = false;
            document.getElementById('loginNav').textContent =
                '🔐 Iniciar sesión';

            document.getElementById('registerNav').hidden = false;
            document.getElementById('profileNav').hidden = true;

            throw new Error(
                'Tu sesión expiró. Inicia sesión nuevamente.'
            );
        }

        if (!respuesta.ok) {
            throw new Error(
                typeof resultado.detail === 'string'
                    ? resultado.detail
                    : 'No se pudo guardar el pedido.'
            );
        }

        // Mostrar confirmación del servidor
        aviso.textContent =
            '✅ ¡Pedido #' + resultado.pedido_id +
            ' registrado correctamente! Total: ' +
            money(resultado.total) +
            '. No se realizó ningún cobro.';

        // Vaciar el carrito SOLO si el servidor confirmó el pedido
        cart = {};
        renderCart();

        console.log('Pedido registrado correctamente');

    } catch (error) {
        aviso.textContent = '❌ ' + error.message;

    } finally {
        boton.disabled = Object.keys(cart).length === 0;
    }

});


async function cargarProductos() {
  try {
    const respuesta = await fetch('/productos');

    if (!respuesta.ok) {
      throw new Error('No se pudieron cargar los productos');
    }

    products = await respuesta.json();

    cart = Object.fromEntries(
      Object.entries(cart).filter(([id]) =>
        products.some(p => String(p.id) === id)
      )
    );

    renderFilters();
    renderProducts();
    renderCart();

    console.log('Productos cargados desde FastAPI:', products.length);

  } catch (error) {
    console.error('Error al conectar con FastAPI:', error);
    $('products').textContent =
      'No se pudieron cargar los productos. Comprueba que el servidor esté encendido.';
  }
}

cargarProductos();


/* LOGIN Y REGISTRO - CAFÉ OMEGA */

const authDialog = document.getElementById('authDialog');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

let cerrandoDialogo = false;

function mostrarFormulario(tipo) {
    const esLogin = tipo === 'login';

    loginForm.hidden = !esLogin;
    registerForm.hidden = esLogin;

    document.getElementById('showLogin')
        .classList.toggle('active', esLogin);

    document.getElementById('showRegister')
        .classList.toggle('active', !esLogin);

    document.getElementById('authMessage').textContent = '';

    if (!authDialog.open) {
        authDialog.showModal();
    }
}

function cerrarFormulario() {
    if (!authDialog.open || cerrandoDialogo) return;

    cerrandoDialogo = true;
    authDialog.classList.add('closing');

    setTimeout(() => {
        authDialog.close();
        authDialog.classList.remove('closing');
        cerrandoDialogo = false;
    }, 220);
}

// Botones de navegación
document.getElementById('loginNav')
    .addEventListener('click', () => mostrarFormulario('login'));

document.getElementById('registerNav')
    .addEventListener('click', () => mostrarFormulario('register'));

// Cambiar entre formularios
document.getElementById('showLogin')
    .addEventListener('click', () => mostrarFormulario('login'));

document.getElementById('showRegister')
    .addEventListener('click', () => mostrarFormulario('register'));

// Cerrar ventana
document.getElementById('closeAuth')
    .addEventListener('click', cerrarFormulario);

// Cerrar al presionar Escape
authDialog.addEventListener('cancel', (event) => {
    event.preventDefault();
    cerrarFormulario();
});

// Cerrar haciendo clic fuera del formulario
authDialog.addEventListener('click', (event) => {
    if (event.target === authDialog) {
        cerrarFormulario();
    }
});

console.log('Sistema visual de autenticación iniciado');



registerForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const mensaje = document.getElementById('authMessage');
    const boton = registerForm.querySelector('button[type="submit"]');

    const datos = {
        nombre: document.getElementById('registerName').value.trim(),
        email: document.getElementById('registerEmail').value.trim(),
        password: document.getElementById('registerPassword').value
    };

    boton.disabled = true;
    mensaje.textContent = 'Creando tu cuenta...';

    try {
        const respuesta = await fetch('/registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            if (respuesta.status === 409) {
                throw new Error('Este correo ya está registrado.');
            }

            throw new Error(
                typeof resultado.detail === 'string'
                    ? resultado.detail
                    : 'Comprueba los datos del formulario.'
            );
        }

        mensaje.textContent =
            '✅ ¡Cuenta creada correctamente! Ahora puedes iniciar sesión.';

        registerForm.reset();

    } catch (error) {
        mensaje.textContent = '❌ ' + error.message;
    } finally {
        boton.disabled = false;
    }
})



document.getElementById('loginForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const formulario = event.currentTarget;
    const mensaje = document.getElementById('authMessage');
    const boton = formulario.querySelector('button[type="submit"]');

    const datos = {
        email: document.getElementById('loginEmail').value.trim(),
        password: document.getElementById('loginPassword').value
    };

    boton.disabled = true;
    mensaje.textContent = 'Iniciando sesión...';

    try {
        const respuesta = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                respuesta.status === 401
                    ? 'Correo o contraseña incorrectos.'
                    : 'No se pudo iniciar sesión.'
            );
        }

        // Guardar la sesión temporalmente en memoria
        window.cafeOmegaSesion = {
            token: resultado.access_token,
            usuario: resultado.usuario
        };

        mensaje.textContent = '✅ ¡Inicio de sesión exitoso!';
        formulario.reset();

        // Actualizar los botones de navegación
        if (resultado.usuario && resultado.usuario.nombre) {
            document.getElementById('loginNav').textContent =
                '👤 ' + resultado.usuario.nombre;
        }

        document.getElementById('registerNav').hidden = true;
        document.getElementById('loginNav').hidden = true;
        document.getElementById('profileNav').hidden = false;

    } catch (error) {
        mensaje.textContent = '❌ ' + error.message;
    } finally {
        boton.disabled = false;
    }
});


/* =========================================
   PERFIL Y CIERRE DE SESIÓN - CAFÉ-OMEGA
========================================= */

const profileButton = document.getElementById('profileNav');
const profileWindow = document.getElementById('profileDialog');
const profileCloseButton = document.getElementById('closeProfile');
const logoutButton = document.getElementById('logoutBtn');

// Abrir perfil
profileButton.addEventListener('click', () => {
    const sesion = window.cafeOmegaSesion;

    if (!sesion || !sesion.usuario) {
        alert('Debes iniciar sesión primero.');
        return;
    }

    const usuario = sesion.usuario;

    document.getElementById('profileName').textContent =
        usuario.nombre || 'Cliente';

    document.getElementById('profileEmail').textContent =
        usuario.email || 'No disponible';

    if (!profileWindow.open) {
        profileWindow.showModal();
    }
});

// Cerrar ventana
profileCloseButton.addEventListener('click', () => {
    profileWindow.close();
});

// Cerrar sesión
logoutButton.addEventListener('click', () => {
    window.cafeOmegaSesion = null;

    const loginButton = document.getElementById('loginNav');
    const registerButton = document.getElementById('registerNav');

    loginButton.textContent = '🔐 Iniciar sesión';
    loginButton.hidden = false;

    registerButton.hidden = false;
    profileButton.hidden = true;

    profileWindow.close();

    console.log('Sesión cerrada correctamente');
});


/* =====================================
   VIDEOS AUTOMÁTICOS - CAFÉ-OMEGA
===================================== */

const omegaVideo = document.getElementById('heroVideo');

const listaVideos = [
    '/cafeteria/videos/cafe1.mp4',
    '/cafeteria/videos/cafe2.mp4',
    '/cafeteria/videos/cafe3.mp4'
];

let indiceVideo = 0;

function cambiarVideoOmega() {
    if (!omegaVideo) return;

    // Ocultar suavemente el video actual
    omegaVideo.classList.add('video-changing');

    setTimeout(() => {
        // Pasar al siguiente video
        indiceVideo = (indiceVideo + 1) % listaVideos.length;

        omegaVideo.src = listaVideos[indiceVideo];
        omegaVideo.load();

        // Reproducir el siguiente
        omegaVideo.play().catch(error => {
            console.warn('No se pudo reproducir el video:', error);
        });

        // Mostrarlo suavemente
        omegaVideo.classList.remove('video-changing');

    }, 550);
}

if (omegaVideo) {

    // Cambiar al terminar cada video
    omegaVideo.addEventListener('ended', cambiarVideoOmega);

    // Mantener el video silenciado
    omegaVideo.muted = true;

    // Iniciar el primer video
    if (!window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    ).matches) {
        omegaVideo.play().catch(() => {});
    }

    console.log('🎬 Sistema de videos Café-Omega iniciado');
}
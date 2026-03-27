let eventsData = [];
let currentLang = 'en';
let currentUiDict = {};
let isTrendingMode = false;
let currentCategoryFilter = 'all';

function getFilteredEvents(excludeUserLoc = false) {
    let displayed = eventsData;
    if (excludeUserLoc) {
        displayed = displayed.filter(e => e.type !== 'user');
    }
    
    if (isTrendingMode) {
        displayed = displayed.filter(e => e.type === 'user' || e.trending);
    }
    
    if (currentCategoryFilter !== 'all') {
        displayed = displayed.filter(e => e.type === 'user' || e.type === currentCategoryFilter);
    }
    
    return displayed;
}

// Initialize UI
const cardsContainer = document.getElementById('event-cards-container');
const detailPanel = document.getElementById('event-detail');
const closeBtn = document.querySelector('.close-btn');

// Render Cards
function renderCards() {
    cardsContainer.innerHTML = '';
    
    let displayedEvents = getFilteredEvents();
    
    displayedEvents.forEach(ev => {
        if (ev.type === 'user') return;
        
        const card = document.createElement('div');
        card.className = `event-card type-${ev.type}`;
        card.onclick = () => showEventDetail(ev);
        
        const sourceIcon = ev.source === 'tiktok' ? 'icon-tiktok' : 'icon-insta';
        
        card.innerHTML = `
            <div class="event-card-header">
                <span class="event-source ${sourceIcon}">${ev.sourceName}</span>
                <span class="event-price">${ev.price}</span>
            </div>
            <h3 class="event-title">${ev.title}</h3>
            <div class="event-meta">
                <span>📍 ${ev.location}</span>
                <span>🕒 ${ev.date}</span>
            </div>
        `;
        cardsContainer.appendChild(card);
    });
}

// Show Detail Modal
function showEventDetail(ev) {
    const content = detailPanel.querySelector('.event-content');
    content.innerHTML = `
        <div class="video-embed-wrapper">
            <iframe src="${ev.embedUrl}" width="100%" height="450" frameborder="0" scrolling="no" allowtransparency="true" allow="fullscreen" title="Social Video"></iframe>
        </div>
        <h2 class="detail-title">${ev.title}</h2>
        <div class="detail-meta">
            <div class="meta-item">
                <span class="meta-label">${currentUiDict.detail_location || 'Location'}</span>
                <span class="meta-value">${ev.location}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">${currentUiDict.detail_date || 'Date & Time'}</span>
                <span class="meta-value">${ev.date}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">${currentUiDict.detail_cost || 'Cost'}</span>
                <span class="meta-value price" style="color: #4CAF50;">${ev.price}</span>
            </div>
        </div>
        <p class="detail-desc">${ev.desc}</p>
        <button class="detail-cta" style="margin-bottom: 12px; background: #00ff88; color: #000;" onclick="viewOnMap()">${currentUiDict.detail_map_btn || 'View Ubication on Map & Routes'}</button>
        <button class="detail-cta" style="margin-bottom: 12px; background: #000; color: #fff; border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s;" onmouseover="this.style.background='#111'; this.style.borderColor='#fff'" onmouseout="this.style.background='#000'; this.style.borderColor='rgba(255,255,255,0.2)'" onclick="requestUber()">${currentUiDict.detail_uber_btn || '🚗 Get Ride with Uber'}</button>
        <button class="detail-cta" style="background: transparent; border: 1px solid var(--glass-border); color: var(--text-primary);">${currentUiDict.detail_info_btn || 'Get Info / Tickets'}</button>
    `;
    detailPanel.classList.remove('hidden');
    currentEvent = ev;
    
    // Focus globe on the event location
    if(world) {
        world.pointOfView({ lat: ev.coords[0], lng: ev.coords[1], altitude: 0.8 }, 1500);
    }
}

closeBtn.onclick = () => {
    detailPanel.classList.add('hidden');
    
    // Zoom out globe back to Medellín general, further away to avoid pixelation
    if(world) {
         world.pointOfView({ lat: 6.2442, lng: -75.5812, altitude: 2.8 }, 1500);
    }
};

function generateRoutes(start, end) {
    currentRoutes.forEach(r => r.remove());
    currentRoutes = [];
    
    const latDiff = end[0] - start[0];
    const lngDiff = end[1] - start[1];
    const dist = Math.sqrt(latDiff*latDiff + lngDiff*lngDiff);
    
    // Green (Good) Route
    const r1 = L.polyline([
        start,
        [start[0] + latDiff * 0.5 + (dist * 0.05), start[1] + lngDiff * 0.5 - (dist * 0.05)],
        end
    ], {color: '#00ff88', weight: 4, dashArray: '10,10', opacity: 0.8}).addTo(leafletMap);
    
    // Yellow (Mid) Route
    const r2 = L.polyline([
        start,
        [start[0] + latDiff * 0.4 - (dist * 0.1), start[1] + lngDiff * 0.6 + (dist * 0.1)],
        [start[0] + latDiff * 0.8 - (dist * 0.05), start[1] + lngDiff * 0.9 + (dist * 0.05)],
        end
    ], {color: '#ffdd00', weight: 4, opacity: 0.6}).addTo(leafletMap);
    
    // Red (Bad) Route
    const r3 = L.polyline([
        start,
        [start[0] + latDiff * 0.2 + (dist * 0.2), start[1] + lngDiff * 0.2 - (dist * 0.2)],
        [start[0] + latDiff * 0.7 + (dist * 0.25), start[1] + lngDiff * 0.5 - (dist * 0.2)],
        end
    ], {color: '#ff3232', weight: 4, opacity: 0.5}).addTo(leafletMap);
    
    currentRoutes.push(r1, r2, r3);
    
    // Fit bounds to display both the user and the event and all 3 routes comfortably
    leafletMap.fitBounds(L.latLngBounds([start, end]).pad(0.3));
}

function viewOnMap() {
    if(!currentEvent) return;
    
    isGlobalMap = false;
    // Hide panel and globe, show map
    document.getElementById('event-detail').classList.add('hidden');
    document.getElementById('globe-container').classList.add('globe-hidden');
    document.getElementById('map-ui-wrapper').classList.remove('map-hidden');
    
    if(!leafletMap) initLeaflet();
    
    if (leafletMarker && !leafletMap.hasLayer(leafletMarker)) {
        leafletMarker.addTo(leafletMap);
    }
    
    const evCoords = currentEvent.coords;
    
    // Set map element for event location
    const color = currentEvent.type === 'music' ? '#ff3232' : currentEvent.type === 'art' ? '#3296ff' : '#ffb432';
    const icon = currentEvent.type === 'music' ? '🎵' : currentEvent.type === 'art' ? '🎨' : '🍽️';
    leafletMarker.setLatLng(evCoords);
    leafletMarker.setIcon(L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
            <div class="custom-marker-wrapper" style="--pin-color: ${color};">
                <div class="marker-pin">
                    <span class="marker-icon">${icon}</span>
                </div>
                <div class="marker-label">
                    <span class="marker-title">${currentEvent.title}</span>
                    <span class="marker-price">${currentEvent.price}</span>
                </div>
            </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
    }));
    
    // Draw 3 fake generated routes from context
    if (userLocation) {
        generateRoutes(userLocation, evCoords);
    } else {
        generateRoutes([6.2300, -75.5800], evCoords); // Fallback to Poblado center
    }
    
    setTimeout(() => {
        leafletMap.invalidateSize();
    }, 100);
}

function closeMap() {
    // Jump back out of Map state
    document.getElementById('map-ui-wrapper').classList.add('map-hidden');
    document.getElementById('globe-container').classList.remove('globe-hidden');
    
    if (!isGlobalMap) {
        document.getElementById('event-detail').classList.remove('hidden');
    } else {
        document.getElementById('event-detail').classList.add('hidden');
    }
}

function viewGlobalMap() {
    isGlobalMap = true;
    document.getElementById('event-detail').classList.add('hidden');
    document.getElementById('globe-container').classList.add('globe-hidden');
    document.getElementById('map-ui-wrapper').classList.remove('map-hidden');
    
    if(!leafletMap) initLeaflet();
    
    // Clear routes and specific marker
    currentRoutes.forEach(r => r.remove());
    currentRoutes = [];
    if (leafletMarker) leafletMarker.remove();
    
    // Clear old global markers
    globalMarkers.forEach(m => m.remove());
    globalMarkers = [];
    
    let displayedEvents = getFilteredEvents();
    
    displayedEvents.forEach(ev => {
        if(ev.type === 'user') return;
        
        const color = ev.type === 'music' ? '#ff3232' : ev.type === 'art' ? '#3296ff' : '#ffb432';
        const icon = ev.type === 'music' ? '🎵' : ev.type === 'art' ? '🎨' : '🍽️';
        const m = L.marker(ev.coords, {
            icon: L.divIcon({
                className: 'custom-leaflet-marker',
                html: `
                    <div class="custom-marker-wrapper" style="--pin-color: ${color};">
                        <div class="marker-pin">
                            <span class="marker-icon">${icon}</span>
                        </div>
                        <div class="marker-label">
                            <span class="marker-title">${ev.title}</span>
                            <span class="marker-price">${ev.price}</span>
                        </div>
                    </div>
                `,
                iconSize: [32, 32],
                iconAnchor: [16, 32]
            })
        }).addTo(leafletMap);
        
        m.on('click', () => {
            showEventDetail(ev);
        });
        
        globalMarkers.push(m);
    });
    
    leafletMap.setView([6.2442, -75.5812], 13);
    setTimeout(() => leafletMap.invalidateSize(), 100);
}

function requestUber() {
    if(!currentEvent) return;
    
    const lat = currentEvent.coords[0];
    const lng = currentEvent.coords[1];
    
    // Construct the universal link with precise pickup and dropoff coordinates
    const dropoffName = encodeURIComponent(currentEvent.title + " (" + currentEvent.location + ")");
    const uberUrl = `https://m.uber.com/ul/?action=setPickup&pickup=my_location&dropoff[latitude]=${lat}&dropoff[longitude]=${lng}&dropoff[nickname]=${dropoffName}`;
    
    // Copy the location text softly in the background as a backup for the user
    try {
        navigator.clipboard.writeText(currentEvent.location);
    } catch(err) {
        console.log("Clipboard fallback unavailable", err);
    }
    
    // Open Uber app (or web booking if no app installed) gracefully
    window.open(uberUrl, '_blank');
}

function toggleTrending() {
    isTrendingMode = !isTrendingMode;
    const trendingBtn = document.getElementById('ui-nav-trending');
    
    if(isTrendingMode) {
        trendingBtn.style.color = '#ffb432';
        trendingBtn.style.textShadow = '0 0 10px rgba(255, 180, 50, 0.8)';
    } else {
        trendingBtn.style.color = '';
        trendingBtn.style.textShadow = '';
    }
    
    renderCards();
    
    if (isGlobalMap) {
        viewGlobalMap();
    } else {
        if(world) {
            world.htmlElementsData(getFilteredEvents());
        }
    }
}

function exploreRandomEvent() {
    if(!eventsData || eventsData.length === 0) return;
    
    if (isGlobalMap || !document.getElementById('map-ui-wrapper').classList.contains('map-hidden')) {
        closeMap();
    }
    
    const validEvents = eventsData.filter(e => e.type !== 'user');
    if(validEvents.length === 0) return;
    
    const randomEvent = validEvents[Math.floor(Math.random() * validEvents.length)];
    detailPanel.classList.add('hidden');
    
    if(world) {
        // Cinematic arc flight
        world.pointOfView({ lat: randomEvent.coords[0], lng: randomEvent.coords[1], altitude: 2.8 }, 2000);
        setTimeout(() => {
            showEventDetail(randomEvent);
        }, 2100);
    } else {
        showEventDetail(randomEvent);
    }
}

// Map container references
const globeContainer = document.getElementById('globe-container');
let world;
let leafletMap;
let leafletMarker;
let userLocation = null;
let currentEvent = null;
let currentRoutes = [];
let globalMarkers = [];
let isGlobalMap = false;

function initLeaflet() {
    leafletMap = L.map('map-container', { 
        zoomControl: false, 
        attributionControl: false 
    }).setView([6.2442, -75.5812], 15);
    
    // Using CARTO Dark Matter for a seamless dark-theme integration
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20
    }).addTo(leafletMap);
    
    const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="width: 24px; height: 24px; background: #00ff88; border-radius: 50%; box-shadow: 0 0 20px #00ff88, inset 0 0 5px #fff; border: 2px solid #fff;"></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    leafletMarker = L.marker([6.2442, -75.5812], {icon: customIcon}).addTo(leafletMap);
}

// Text Pull-up Animation Generator
function initTextAnimation(selector) {
    const el = document.querySelector(selector);
    if (!el) return;
    const text = el.innerText;
    el.innerHTML = '';
    
    // Wrap each word in an overflow:hidden mask for the pull-up effect
    const words = text.split(' ');
    words.forEach((word, wordIdx) => {
        const wordWrap = document.createElement('span');
        wordWrap.className = 'word-wrap';
        
        word.split('').forEach((char, i) => {
            const span = document.createElement('span');
            span.className = 'char-pull-up';
            // Stagger each letter's animation slightly
            span.style.animationDelay = `${(wordIdx * 0.1) + (i * 0.04)}s`;
            span.innerText = char;
            wordWrap.appendChild(span);
        });
        
        el.appendChild(wordWrap);
        if(wordIdx < words.length - 1) el.innerHTML += ' ';
    });
}

function updateUiTexts(ui) {
    currentUiDict = ui;
    if(document.getElementById('ui-nav-events')) document.getElementById('ui-nav-events').innerText = ui.nav_events;
    if(document.getElementById('ui-nav-map')) document.getElementById('ui-nav-map').innerText = ui.nav_map;
    if(document.getElementById('ui-nav-trending')) document.getElementById('ui-nav-trending').innerText = ui.nav_trending;
    if(document.getElementById('ui-nav-explore')) document.getElementById('ui-nav-explore').innerText = ui.nav_explore;
    
    const heroTitle = document.getElementById('ui-hero-title');
    if(heroTitle) {
        heroTitle.innerText = ui.hero_title;
        // Re-run the pull-up animation after changing text
        initTextAnimation('#ui-hero-title');
    }
    
    if(document.getElementById('ui-hero-sub')) document.getElementById('ui-hero-sub').innerText = ui.hero_sub;
    if(document.getElementById('ui-back-btn')) document.getElementById('ui-back-btn').innerHTML = `&larr; ${ui.back_btn}`;
}

function fetchEventsAndRender(lang) {
    const isAdmin = currentUser && currentUser.role === 'admin' ? 'true' : 'false';
    fetch(`/api/events?lang=${lang}&admin=${isAdmin}`)
        .then(res => res.json())
        .then(data => {
            eventsData = data.events;
            updateUiTexts(data.ui);
            renderCards();
            
            // Re-bind to globe if globe is running to update markers/labels
            if(world) {
                // Keep the user location dot if present
                if (userLocation) {
                    const idx = eventsData.findIndex(e => e.id === 'user-loc');
                    if (idx === -1) {
                         eventsData.push({
                            id: 'user-loc',
                            type: 'user',
                            coords: userLocation,
                            title: data.ui.user_location
                        });
                    }
                }
                world.htmlElementsData(getFilteredEvents());
            }
        })
        .catch(err => console.error("Error fetching events:", err));
}

document.addEventListener('DOMContentLoaded', () => {
    // Listen to Language Switcher
    const langSwitcher = document.getElementById('lang-switcher');
    if(langSwitcher) {
        langSwitcher.addEventListener('change', (e) => {
            currentLang = e.target.value;
            fetchEventsAndRender(currentLang);
            if(detailPanel && !detailPanel.classList.contains('hidden') && currentEvent) {
                // If modal is open, try to update it instantly by finding the translated event
                const transEv = eventsData.find(ev => ev.id === currentEvent.id);
                if(transEv) showEventDetail(transEv);
            }
        });
    }

    // Initial fetch
    fetchEventsAndRender(currentLang);
    
    // Initialize Globe.gl
    // Add realistic 3D earth visually mapping to our coordinates
    world = Globe()(globeContainer)
      .globeImageUrl('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
      .bumpImageUrl('https://unpkg.com/three-globe/example/img/earth-topology.png')
      .backgroundImageUrl('https://unpkg.com/three-globe/example/img/night-sky.png')
      .showAtmosphere(true)
      .atmosphereColor('#3a228a')
      .atmosphereAltitude(0.25)
      .backgroundColor('rgba(0,0,0,0)') // Transparent to blend better
      .width(window.innerWidth)
      .height(window.innerHeight * 1.3)
      .pointOfView({ lat: 0, lng: 0, altitude: 4 }) // Start far away for cinematic intro
      .htmlElementsData(eventsData)
      .htmlElement(d => {
        if (d.type === 'user') {
            const el = document.createElement('div');
            el.innerHTML = `<div style="width: 20px; height: 20px; background: #00ff88; border-radius: 50%; box-shadow: 0 0 20px #00ff88, inset 0 0 5px #fff; border: 2px solid #fff; transform: translate(-50%, -50%); animation: pulse 2s infinite;"></div>`;
            return el;
        }

        const el = document.createElement('div');
        // Add a glowing dot for each event on the 3D globe
        const color = d.type === 'music' ? '#ff3232' : d.type === 'art' ? '#3296ff' : '#ffb432';
        el.innerHTML = `<div style="width: 24px; height: 24px; background: ${color}; border-radius: 50%; box-shadow: 0 0 20px ${color}, inset 0 0 5px #fff; border: 2px solid #fff; cursor: pointer; transform: translate(-50%, -50%); transition: transform 0.2s ease;" onmouseover="this.style.transform='scale(1.2) translate(-50%, -50%)'" onmouseout="this.style.transform='scale(1) translate(-50%, -50%)'"></div>`;
        el.onclick = () => showEventDetail(d);
        return el;
      });

    // Background and Planets removed by request to fix rendering issues

    // Intro Animation
    setTimeout(() => {
        // Fly from space into Medellin at a comfortable distance
        world.pointOfView({ lat: 6.2442, lng: -75.5812, altitude: 2.8 }, 4000);
        
        // After intro, ask for geolocation
        setTimeout(() => {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition((position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    userLocation = [lat, lng];
                    
                    // Add user location marker
                    const userLocTitle = currentUiDict && currentUiDict.user_location ? currentUiDict.user_location : 'You are here';
                    eventsData.push({
                        id: 'user-loc',
                        type: 'user',
                        coords: [lat, lng],
                        title: userLocTitle
                    });
                    
                    world.htmlElementsData(eventsData);
                    // Fly to the user!
                    world.pointOfView({ lat: lat, lng: lng, altitude: 2.8 }, 2000);
                }, (err) => {
                    console.warn('Geolocation blocked or failed', err);
                });
            }
        }, 4500); // 4.5 seconds after intro started
    }, 500);

    // Interaction controls for globe
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.25; // Slow, majestic cinematic spin
    world.controls().enableZoom = true;
    world.controls().zoomSpeed = 0.8;
    world.controls().minDistance = 110; // Allowed extreme zoom closely for 1080p+ detailed view
    world.controls().maxDistance = 500;

    // Handle Resize
    window.addEventListener('resize', () => {
        if(world) {
            world.width(window.innerWidth).height(window.innerHeight * 1.3);
        }
    });

    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if(e.key === 'Escape') {
            closeBtn.click();
            closeGallery();
        }
    });
});

// --- Immersive Events Gallery Logic ---
function showEventsGallery() {
    if (isGlobalMap || !document.getElementById('map-ui-wrapper').classList.contains('map-hidden')) {
        closeMap();
    }
    document.getElementById('events-gallery').classList.remove('gallery-hidden');
    renderGallery();
}

function closeGallery() {
    document.getElementById('events-gallery').classList.add('gallery-hidden');
}

function setCategoryFilter(category) {
    currentCategoryFilter = category;
    
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if(btn.getAttribute('data-filter') === category) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    renderCards();
    renderGallery();
    
    if (isGlobalMap) {
        viewGlobalMap();
    } else {
        if (world) {
            world.htmlElementsData(getFilteredEvents());
        }
    }
}

function renderGallery() {
    const grid = document.getElementById('gallery-grid-container');
    if(!grid) return;
    grid.innerHTML = '';
    
    const eventsToRender = getFilteredEvents(true); // Exclude user-loc
    
    eventsToRender.forEach(ev => {
        const card = document.createElement('div');
        card.className = 'gallery-card';
        card.onclick = () => {
            closeGallery();
            showEventDetail(ev);
        };
        
        card.innerHTML = `
            <div class="gallery-card-img-wrapper">
                <img src="${ev.image || 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30'}" class="gallery-card-img" alt="${ev.title}">
            </div>
            <div class="gallery-card-info">
                <h3 class="gallery-card-title">${ev.title}</h3>
                <p style="font-size: 0.9rem; color: #ccc; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${ev.desc}</p>
                <div class="gallery-card-meta">
                    <span>${ev.date}</span>
                    <span class="gallery-card-price">${ev.price}</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

// --- Authentication & Role Management ---
let currentUser = null; // { id, email, role }
let authMode = 'login'; // 'login' | 'register'

function openAuthModal(mode) {
    authMode = mode;
    updateAuthUI();
    document.getElementById('auth-modal').classList.remove('hidden');
    document.getElementById('auth-error').style.display = 'none';
}

function closeAuthModal() {
    document.getElementById('auth-modal').classList.add('hidden');
}

function toggleAuthMode() {
    authMode = authMode === 'login' ? 'register' : 'login';
    updateAuthUI();
}

function updateAuthUI() {
    const title = document.getElementById('auth-title');
    const toggleText = document.getElementById('auth-toggle-text');
    if(authMode === 'login') {
        title.innerText = 'Log In';
        toggleText.innerHTML = 'Need an account? <b>Sign Up</b>';
    } else {
        title.innerText = 'Sign Up';
        toggleText.innerHTML = 'Already have an account? <b>Log In</b>';
    }
}

async function submitAuth() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;
    const errorMsg = document.getElementById('auth-error');
    
    if(!email || !password) {
        errorMsg.innerText = "Please fill in all fields.";
        errorMsg.style.display = 'block';
        return;
    }
    
    // Admin override check (harding admin registering if we want to restrict, but backend handles it via email check or we just let anyone register 'user')
    const endpoint = authMode === 'login' ? '/api/login' : '/api/register';
    const payload = { email, password, role: 'user' }; // defaults to user
    
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if(data.success) {
            currentUser = data.user;
            closeAuthModal();
            updateNavbarForUser();
            // Re-fetch events (Admins will now see 'pending' events if we pass admin flag)
            if(currentUser.role === 'admin') fetchEventsAndRender();
        } else {
            errorMsg.innerText = data.message || "Authentication failed.";
            errorMsg.style.display = 'block';
        }
    } catch(e) {
        errorMsg.innerText = "Server connection error.";
        errorMsg.style.display = 'block';
    }
}

// Intercept Enter key for Auth
document.getElementById('auth-password').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') submitAuth();
});

function updateNavbarForUser() {
    const authContainer = document.getElementById('auth-container');
    const userMenu = document.getElementById('user-menu-container');
    
    if(currentUser) {
        authContainer.classList.add('hidden');
        userMenu.classList.remove('hidden');
        document.getElementById('user-name-display').innerText = currentUser.email.split('@')[0];
        
        const orgBtn = document.getElementById('organizer-dash-btn');
        const adminBtn = document.getElementById('admin-dash-btn');
        
        if(currentUser.role === 'admin') {
            adminBtn.classList.remove('hidden');
            orgBtn.classList.add('hidden');
        } else if(currentUser.role === 'organizer') {
            orgBtn.classList.remove('hidden');
            orgBtn.innerText = "Dashboard";
            adminBtn.classList.add('hidden');
        } else {
            // Normal user -> offer upgrade
            orgBtn.classList.remove('hidden');
            orgBtn.innerText = "Upgrade ($2/mo)";
            adminBtn.classList.add('hidden');
        }
        
    } else {
        authContainer.classList.remove('hidden');
        userMenu.classList.add('hidden');
        // Go back to standard view if logged out as admin
        fetchEventsAndRender();
    }
}

function logoutUser() {
    currentUser = null;
    updateNavbarForUser();
}

async function openOrganizerDash() {
    if(currentUser.role === 'user') {
        // Bypass blocking native browser prompts to ensure reliability
        try {
            await fetch('/api/user/upgrade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: currentUser.id })
            });
        } catch(e) {
            console.log(e);
        }
        currentUser.role = 'organizer';
        updateNavbarForUser();
        // Automatically open the form
        document.getElementById('organizer-modal').classList.remove('hidden');
    } else if(currentUser.role === 'organizer') {
        document.getElementById('organizer-modal').classList.remove('hidden');
    }
}

function openAdminDash() {
    if(currentUser.role !== 'admin') return;
    document.getElementById('admin-modal').classList.remove('hidden');
    renderAdminTable();
}

async function submitOrganizerEvent() {
    const title = document.getElementById('org-title').value;
    const location = document.getElementById('org-location').value;
    const lat = parseFloat(document.getElementById('org-lat').value);
    const lng = parseFloat(document.getElementById('org-lng').value);
    const date = document.getElementById('org-date').value;
    const price = document.getElementById('org-price').value;
    const type = document.getElementById('org-type').value;
    const image = document.getElementById('org-image').value;
    const desc = document.getElementById('org-desc').value;

    if(!title || !location || !lat || !lng || !date || !price || !type || !image || !desc) {
        alert("Please fill all fields!");
        return;
    }

    const payload = {
        title, location, lat, lng, date, price, type, image, desc, organizer_id: currentUser.id
    };

    try {
        const res = await fetch('/api/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if(data.success) {
            alert("Event successfully submitted! An admin will review it shortly before it goes live.");
            document.getElementById('organizer-modal').classList.add('hidden');
            document.getElementById('org-title').value = '';
        } else {
            alert("Error submitting event: " + data.message);
        }
    } catch (e) {
        alert("Server error.");
    }
}

async function renderAdminTable() {
    const container = document.getElementById('admin-table-container');
    container.innerHTML = '<p>Loading pending events...</p>';
    
    try {
        const lang = document.getElementById('lang-switcher')?.value || 'en';
        const res = await fetch(`/api/events?lang=${lang}&admin=true`);
        const data = await res.json();
        const pendingEvents = data.events.filter(e => e.status === 'pending');
        
        if(pendingEvents.length === 0) {
            container.innerHTML = '<p style="color:#00ff88;">All caught up! No pending events.</p>';
            return;
        }

        let html = `<table style="width:100%; text-align:left; border-collapse: collapse; margin-top:10px; font-family: 'Inter';">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.2);">
                <th style="padding:10px;">ID</th>
                <th style="padding:10px;">Title</th>
                <th style="padding:10px;">Category</th>
                <th style="padding:10px;">Source</th>
                <th style="padding:10px;">Actions</th>
            </tr>`;
            
        pendingEvents.forEach(ev => {
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding:10px; color:rgba(255,255,255,0.5); font-size: 12px;">${ev.id}</td>
                <td style="padding:10px; font-weight:bold;">${ev.title}</td>
                <td style="padding:10px;">${ev.type}</td>
                <td style="padding:10px; font-size: 12px; color: rgba(255,255,255,0.4);">${ev.source || 'custom'}</td>
                <td style="padding:10px; display:flex; gap:10px;">
                    <button class="cta-pill" style="padding: 6px 15px; font-size:12px; min-width:80px; background:#00ff88; color:black; border:none; border-radius: 20px; cursor: pointer; font-weight: 700;" onclick="verifyEvent('${ev.id}')">Approve</button>
                    <button class="cta-pill" style="padding: 6px 15px; font-size:12px; min-width:80px; background:#ff3232; color:white; border:none; border-radius: 20px; cursor: pointer; font-weight: 700;" onclick="rejectEvent('${ev.id}')">Reject</button>
                </td>
            </tr>`;
        });
        html += '</table>';
        container.innerHTML = html;
    } catch(e) {
        container.innerHTML = '<p style="color:#ff3232;">Error loading events.</p>';
    }
}

async function verifyEvent(id) {
    try {
        await fetch(`/api/admin/verify/${id}`, { method: 'POST' });
        fetchEventsAndRender();
        renderAdminTable();
        loadBotStats();
    } catch(e) {
        alert("Error approving event.");
    }
}

async function rejectEvent(id) {
    try {
        await fetch(`/api/admin/reject/${id}`, { method: 'POST' });
        fetchEventsAndRender();
        renderAdminTable();
        loadBotStats();
    } catch(e) {
        alert("Error rejecting event.");
    }
}

// =========================================
// ADMIN BOT CONTROL PANEL
// =========================================
let trackedAccounts = [];

function switchAdminTab(tab) {
    const eventsTab = document.getElementById('admin-tab-events');
    const botTab = document.getElementById('admin-tab-bot');
    const eventsBtn = document.getElementById('tab-events-btn');
    const botBtn = document.getElementById('tab-bot-btn');
    
    if(tab === 'events') {
        eventsTab.classList.remove('hidden');
        botTab.classList.add('hidden');
        eventsBtn.style.color = 'white';
        eventsBtn.style.borderBottomColor = '#ff3232';
        botBtn.style.color = 'rgba(255,255,255,0.5)';
        botBtn.style.borderBottomColor = 'transparent';
        renderAdminTable();
    } else {
        eventsTab.classList.add('hidden');
        botTab.classList.remove('hidden');
        botBtn.style.color = 'white';
        botBtn.style.borderBottomColor = '#ff3232';
        eventsBtn.style.color = 'rgba(255,255,255,0.5)';
        eventsBtn.style.borderBottomColor = 'transparent';
        loadBotStats();
        loadBotAccounts();
    }
}

async function loadBotStats() {
    try {
        const res = await fetch('/api/bot/stats');
        const data = await res.json();
        if(data.success) {
            document.getElementById('stat-pending').innerText = data.pending;
            document.getElementById('stat-approved').innerText = data.approved;
            document.getElementById('stat-total').innerText = data.total;
        }
    } catch(e) {
        console.log('Stats error:', e);
    }
}

async function loadBotAccounts() {
    try {
        const res = await fetch('/api/bot/accounts');
        const data = await res.json();
        if(data.success) {
            trackedAccounts = data.accounts;
            renderAccountPills();
        }
    } catch(e) {
        console.log('Accounts error:', e);
    }
}

function renderAccountPills() {
    const container = document.getElementById('bot-accounts-list');
    container.innerHTML = trackedAccounts.map((acc, i) => 
        `<span style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 20px; padding: 6px 14px; font-family: 'Inter'; font-size: 13px; color: white;">
            @${acc}
            <span onclick="botRemoveAccount(${i})" style="cursor: pointer; color: #ff3232; font-weight: 900; font-size: 16px; line-height: 1;">&times;</span>
        </span>`
    ).join('');
}

async function botAddAccount() {
    const input = document.getElementById('bot-new-account');
    const name = input.value.trim().replace('@', '');
    if(!name) return;
    
    trackedAccounts.push(name);
    input.value = '';
    renderAccountPills();
    
    await fetch('/api/bot/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accounts: trackedAccounts })
    });
}

async function botRemoveAccount(index) {
    trackedAccounts.splice(index, 1);
    renderAccountPills();
    
    await fetch('/api/bot/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accounts: trackedAccounts })
    });
}

async function botScanUrl() {
    const input = document.getElementById('bot-url-input');
    const result = document.getElementById('bot-scan-result');
    const url = input.value.trim();
    
    if(!url) return;
    
    result.style.display = 'block';
    result.style.color = '#ffb432';
    result.innerText = 'Escaneando con IA... por favor espera...';
    
    try {
        const res = await fetch('/api/bot/scan-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        const data = await res.json();
        
        if(data.success) {
            result.style.color = '#00ff88';
            result.innerText = data.message;
            input.value = '';
            loadBotStats();
            fetchEventsAndRender();
        } else {
            result.style.color = '#ff3232';
            result.innerText = data.message;
        }
    } catch(e) {
        result.style.color = '#ff3232';
        result.innerText = 'Error de conexion con el servidor.';
    }
}

async function botScanAll() {
    const result = document.getElementById('bot-scan-result');
    result.style.display = 'block';
    result.style.color = '#ffb432';
    result.innerText = 'Rastreo masivo iniciado en segundo plano... esto puede tardar unos minutos.';
    
    try {
        const res = await fetch('/api/bot/scan-all', { method: 'POST' });
        const data = await res.json();
        result.style.color = data.success ? '#00ff88' : '#ff3232';
        result.innerText = data.message;
    } catch(e) {
        result.style.color = '#ff3232';
        result.innerText = 'Error lanzando el rastreo.';
    }
}

(() => {
  const categories = [
    ["⚡","Electricistas"],["🚿","Plomeros"],["🔧","Gasfiteros"],["💻","Computadoras"],["📱","Celulares"],["🛠️","Instaladores"],
    ["🏠","Hogar"],["❄️","Refrigeración"],["🎨","Pintores"],["🪚","Carpinteros"],["🚗","Mecánicos"],["＋","Otros"]
  ];
  const technicians = [
    {id:1,name:"Carlos Mendoza",specialty:"Computadoras",city:"Huancayo",area:"Centro de Huancayo",lat:-12.0678,lng:-75.2100,price:45,rating:4.9,experience:6,available:true,about:"Mantenimiento, reparación de laptops y recuperación de equipos.",initials:"CM",review:"Atención clara y puntual.",phone:"51999900101"},
    {id:2,name:"Lucía Rojas",specialty:"Electricistas",city:"Huancayo",area:"San Carlos",lat:-12.0555,lng:-75.2050,price:55,rating:4.8,experience:5,available:true,about:"Instalaciones eléctricas y revisión de tableros domiciliarios.",initials:"LR",review:"Explicó el trabajo y dejó todo ordenado.",phone:"51999900102"},
    {id:3,name:"Miguel Torres",specialty:"Plomeros",city:"El Tambo",area:"El Tambo",lat:-12.0470,lng:-75.2200,price:40,rating:4.7,experience:8,available:false,about:"Reparación de fugas, griferías y mantenimiento de tuberías.",initials:"MT",review:"Solucionó la fuga rápidamente.",phone:"51999900103"},
    {id:4,name:"Andrea Salazar",specialty:"Celulares",city:"Huancayo",area:"La Rivera",lat:-12.0750,lng:-75.1980,price:50,rating:4.9,experience:4,available:true,about:"Diagnóstico y reparación de celulares Android.",initials:"AS",review:"Muy buena comunicación.",phone:"51999900104"},
    {id:5,name:"José Huamán",specialty:"Refrigeración",city:"Chilca",area:"Chilca",lat:-12.0900,lng:-75.2050,price:65,rating:4.8,experience:9,available:true,about:"Mantenimiento de refrigeradoras y equipos de frío.",initials:"JH",review:"Trabajo profesional.",phone:"51999900105"},
    {id:6,name:"Rosa Quispe",specialty:"Carpinteros",city:"El Tambo",area:"El Tambo",lat:-12.0400,lng:-75.2300,price:60,rating:4.6,experience:7,available:true,about:"Muebles a medida, puertas y reparaciones de madera.",initials:"RQ",review:"Buen acabado y trato amable.",phone:"51999900106"}
  ];
  const centers = {
    "Huancayo": {lat:-12.0678,lng:-75.2100},
    "El Tambo": {lat:-12.0470,lng:-75.2200},
    "Chilca": {lat:-12.0900,lng:-75.2050}
  };
  let map = null, geocoder = null, selectedMarker = null, clientLocation = null, markers = [], activeCategory = "Todos";
  const $ = (s) => document.querySelector(s);
  const distanceKm = (a,b) => {
    const rad = (n) => n * Math.PI / 180;
    const dLat = rad(b.lat-a.lat), dLng = rad(b.lng-a.lng);
    const h = Math.sin(dLat/2)**2 + Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(dLng/2)**2;
    return 6371 * 2 * Math.asin(Math.sqrt(h));
  };
  function renderCategories() {
    const root=$("#categoryGrid");
    if(!root)return;
    root.innerHTML=categories.map((c)=>'<button class="category-tile" type="button" data-category="'+c[1]+'"><span>'+c[0]+'</span><strong>'+c[1]+'</strong></button>').join('');
    root.querySelectorAll("button").forEach((b)=>b.addEventListener("click",()=>{
      activeCategory=b.dataset.category;
      $("#techCategory").value=activeCategory==="Todos"?"":activeCategory;
      renderTechnicians();
      $("#tecnicos").scrollIntoView({behavior:"smooth"});
    }));
  }
  function filteredTechnicians() {
    const city=$("#techCity")?.value || "Todas";
    const specialty=$("#techCategory")?.value || "";
    const available=$("#techAvailability")?.checked || false;
    const maxDistance=Number($("#techDistance")?.value || 30);
    return technicians.filter((t)=>{
      if(city!=="Todas" && t.city!==city)return false;
      if(specialty && t.specialty!==specialty)return false;
      if(available && !t.available)return false;
      if(clientLocation && distanceKm(clientLocation,t)>maxDistance)return false;
      return true;
    }).map(t=>({...t,distance:clientLocation?distanceKm(clientLocation,t):null}));
  }
  function renderTechnicians() {
    const root=$("#technicianCards");
    if(!root)return;
    const list=filteredTechnicians();
    root.innerHTML=list.length?list.map(t=>'<article class="pro-card"><div class="pro-card-top"><div class="pro-avatar">'+t.initials+'</div><span class="pro-status '+(t.available?'is-available':'is-busy')+'">'+(t.available?'Disponible':'No disponible')+'</span></div><h3>'+t.name+'</h3><p class="pro-specialty">'+t.specialty+' · '+t.area+'</p><div class="pro-rating">★★★★★ <b>'+t.rating.toFixed(1)+'</b> <span>Perfil de demostración</span></div><p class="pro-about">'+t.about+'</p><div class="pro-meta"><span>'+t.experience+' años de experiencia</span><strong>Desde S/ '+t.price+'</strong></div>'+(t.distance!==null?'<small class="pro-distance">Aprox. '+t.distance.toFixed(1)+' km de tu ubicación</small>':'')+'<p class="pro-review">“'+t.review+'”</p><div class="pro-actions"><button class="button button-primary request-tech" data-id="'+t.id+'">Solicitar servicio</button><a class="button button-outline" href="https://wa.me/'+t.phone+'" target="_blank" rel="noopener">WhatsApp</a></div></article>').join(''):'<div class="empty-state">No encontramos perfiles con esos filtros. Prueba otra especialidad o zona.';
    root.querySelectorAll(".request-tech").forEach((b)=>b.addEventListener("click",()=>{
      const t=technicians.find(x=>x.id===Number(b.dataset.id));
      const booking=$("#contratar");
      if(booking)booking.classList.remove("hidden");
      if($("#ubicacion"))$("#ubicacion").value=t.area+", "+t.city+", Junín";
      if($("#descripcion"))$("#descripcion").value="Solicito atención de "+t.specialty.toLowerCase()+". Técnico de referencia seleccionado: "+t.name+".";
      booking?.scrollIntoView({behavior:"smooth"});
      if(!window.localStorage.getItem("rapijob_token"))$("#authMessage").textContent="Inicia sesión o crea una cuenta para enviar tu solicitud.";
    }));
    renderMarkers(list);
  }
  function renderMarkers(list) {
    if(!map || !window.google?.maps)return;
    markers.forEach(m=>m.setMap(null));markers=[];
    list.forEach(t=>{
      const marker=new google.maps.Marker({map,position:{lat:t.lat,lng:t.lng},title:t.name, label:{text:"●",color:"#ffffff"}});
      const info=new google.maps.InfoWindow({content:'<div style="padding:6px"><b>'+t.name+'</b><br>'+t.specialty+' · '+t.city+'<br>Desde S/ '+t.price+'<br><small>Perfil de demostración</small></div>'});
      marker.addListener("click",()=>info.open({map,anchor:marker}));
      markers.push(marker);
    });
    if(selectedMarker)selectedMarker.setMap(map);
  }
  function setSelectedLocation(latLng, address) {
    const pos={lat:latLng.lat(),lng:latLng.lng()};
    clientLocation=pos;
    if(selectedMarker)selectedMarker.setMap(null);
    selectedMarker=new google.maps.Marker({map,position:pos,title:"Ubicación del servicio",icon:{path:google.maps.SymbolPath.BACKWARD_CLOSED_ARROW,scale:7,fillColor:"#f5b82e",fillOpacity:1,strokeColor:"#17345c",strokeWeight:2}});
    $("#selectedAddress").value=address || pos.lat.toFixed(6)+", "+pos.lng.toFixed(6);
    $("#locationStatus").textContent="Ubicación seleccionada. Las distancias son aproximadas.";
    renderTechnicians();
  }
  window.initRapiJobMap = function() {
    const el=$("#rapijobMap");if(!el||!window.google?.maps)return;
    const center=centers[$("#mapCity")?.value||"Huancayo"];
    map=new google.maps.Map(el,{center,zoom:13,mapTypeControl:false,streetViewControl:false,fullscreenControl:true,styles:[{featureType:"poi",elementType:"labels",stylers:[{visibility:"off"}]}]});
    geocoder=new google.maps.Geocoder();
    map.addListener("click",(event)=>geocoder.geocode({location:event.latLng},(results,status)=>{
      setSelectedLocation(event.latLng,status==="OK"&&results[0]?results[0].formatted_address:"Ubicación elegida en el mapa");
    }));
    renderMarkers(filteredTechnicians());
  };
  async function loadMap() {
    const status=$("#mapStatus");
    try {
      const response=await fetch("/api/config/public");
      const config=await response.json();
      if(!config.google_maps_api_key){
        status.textContent="Para activar Google Maps, configura GOOGLE_MAPS_API_KEY en las variables de entorno de Render. Mientras tanto puedes consultar los perfiles de demostración.";
        return;
      }
      const script=document.createElement("script");
      script.src="https://maps.googleapis.com/maps/api/js?key="+encodeURIComponent(config.google_maps_api_key)+"&callback=initRapiJobMap&language=es&region=PE";
      script.async=true;script.defer=true;script.onerror=()=>status.textContent="No se pudo cargar Google Maps. Revisa la clave API y sus restricciones.";
      document.head.appendChild(script);
    } catch {status.textContent="No se pudo consultar la configuración del mapa.";}
  }
  function initMapControls() {
    $("#mapCity")?.addEventListener("change",()=>{
      const c=centers[$("#mapCity").value];
      if(map&&c){map.setCenter(c);map.setZoom(13);}
      $("#techCity").value=$("#mapCity").value;
      clientLocation=null;renderTechnicians();
    });
    $("#techCity")?.addEventListener("change",()=>{if(map){const c=centers[$("#techCity").value];if(c)map.setCenter(c);}renderTechnicians();});
    ["techCategory","techAvailability","techDistance"].forEach(id=>$("#"+id)?.addEventListener("change",renderTechnicians));
    $("#useMyLocation")?.addEventListener("click",()=>{
      if(!navigator.geolocation){$("#locationStatus").textContent="Tu navegador no permite obtener la ubicación.";return;}
      $("#locationStatus").textContent="Solicitando permiso de ubicación…";
      navigator.geolocation.getCurrentPosition((p)=>{
        const pos=new google.maps.LatLng(p.coords.latitude,p.coords.longitude);
        map?.setCenter(pos);map?.setZoom(15);
        if(geocoder)geocoder.geocode({location:pos},(r,s)=>setSelectedLocation(pos,s==="OK"&&r[0]?r[0].formatted_address:"Ubicación actual"));
      },()=>$("#locationStatus").textContent="No se pudo obtener tu ubicación. Puedes seleccionar un punto en el mapa.",{enableHighAccuracy:true,timeout:10000});
    });
    $("#searchAddress")?.addEventListener("click",()=>{
      const q=$("#addressSearch").value.trim();if(!q||!geocoder)return;
      geocoder.geocode({address:q+", Junín, Perú"},(results,status)=>{
        if(status==="OK"&&results[0]){map.setCenter(results[0].geometry.location);map.setZoom(15);setSelectedLocation(results[0].geometry.location,results[0].formatted_address);}
        else $("#locationStatus").textContent="No encontramos esa dirección. Prueba con otra referencia.";
      });
    });
    $("#useMapAddress")?.addEventListener("click",()=>{
      if($("#selectedAddress").value&&$("#ubicacion")){$("#ubicacion").value=$("#selectedAddress").value;$("#contratar").classList.remove("hidden");$("#contratar").scrollIntoView({behavior:"smooth"});}
    });
  }
  document.addEventListener("DOMContentLoaded",()=>{
    renderCategories();renderTechnicians();initMapControls();loadMap();
    const originalTitle=document.querySelector(".hero h1");
    if(originalTitle)originalTitle.innerHTML='¿Necesitas un técnico? <em>Encuentra uno cerca de ti.</em>';
    const heroText=document.querySelector(".hero-text");
    if(heroText)heroText.textContent="Técnicos confiables, soluciones rápidas. Encuentra profesionales cerca de ti en Huancayo, El Tambo y Chilca.";
    const primary=document.querySelector(".hero-actions .button-primary");
    if(primary){primary.textContent="Solicitar técnico →";primary.href="#explorar-tecnicos";}
    const secondary=document.querySelector(".hero-actions .text-link");
    if(secondary){secondary.textContent="Trabaja como técnico ↓";secondary.href="#acceso";secondary.addEventListener("click",()=>{const type=$("#regTipoUsuario");if(type)type.value="tecnico";});}
  });
})();
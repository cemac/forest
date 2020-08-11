let openId = function(id, width) {
    if (typeof width === "undefined") {
        width = "400px";
    }
    document.getElementById(id).style.width = width;
}
let closeId = function(id) {
    document.getElementById(id).style.width = "0";
};

//globals
const scale = 100
document.bbox = []; // storage for figure ranges
document.fronts = []; // storage for weather fronts
document.n = 1; // number of figures
document.maxfig = 3;// update this manually if forrest allows more plots for comparison
get_figures();


var frontClass = {
    warm: "WW",
    cold: "CC",
    occluded: "WC",
    stationary: "Wc"  // need to add another letter to the font to match 
    
};

// functions

function get_figures() {
    // saves the figure locations in global set_variables
    document.canvases = [
        ...document.querySelectorAll('#figures div[class="bk-root"] canvas')
    ];
    document.canvases = document.canvases
        .filter(function(_, index) {
            return index % 2 === 0;
        })

    // hide irrelevant menus
    try{ hide_menus() }catch (e){
        setTimeout(hide_menus, 2000);
    }
    console.log(document.n, 'figures')
    
    // add svg elements to all canvas grids
    document.svgs = document.canvases.map((d, i) => {
        var parent = d.parentElement;
        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", parent.style.width);
        svg.setAttribute("height", parent.style.height);
        svg.setAttribute("transform", "scale(1,-1)")
        
        /// preserveAspectRatio="xMidYMid meet"
        
        try {
            parent.querySelector("svg").remove();
        } catch (e) {}
        parent.appendChild(svg);
        return svg;
    });



    // load libraries
    try{ get_d3() }catch (e){
        setTimeout(get_d3, 2000);
    }
}

function resize_svg( svg_n ){
    var svg = d3.select(document.svgs[svg_n]);
    var bounds = document.bbox[svg_n]
    
    if (bounds){
    
    w = Math.abs(bounds.x1 - bounds.x0)/scale
    h = Math.abs(bounds.y1 - bounds.y0)/scale

    svg.attr('viewBox',`${bounds.x0/scale} ${bounds.y0/scale} ${w} ${h}`)
    
    }
}


function draw_front(type, svg_n) {
    // the function used for drawing weather fronts
    // Font Available at https://github.com/cemac/WeatherFront
    // contact Dan Ellis (github: wolfiex) for support
    
    // if needed this can be converted into vanilla
    console.log(type)
    
    var svg = d3.select(document.svgs[svg_n]);
    resize_svg(svg_n)
    
    var line = d3.line().curve(d3.curveBasis);
    
    id = document.fronts[type].xs.length
    
    coords = document.fronts[type].xs[id-1].map(function(d,i){
        return [d/scale,document.fronts[type].ys[id-1][i]/scale]
    })
    
    var textPath = svg
        .append("defs")
        .append("path")
        .attr('class',type)
        .attr("id", `textPath_${type}_${id}`)
        .attr("d", line(coords));;


    var text4path = svg
        .append("text")
        .append("textPath")
        .attr("id", `text4path_${type}_${id}`)
        .attr('class',type)
        .attr("xlink:href", `#textPath_${type}_${id}`)
        .text(frontClass[type].repeat(100));
        
    // 
    var path = svg
        .append("use")
        .attr("id", "Path" + id)
        .attr("xlink:href", `#textPath_${type}_${id}`)
        .attr('class',type)

}




/// functions ///
function get_d3(){
    if (typeof d3 == 'undefined') {
        var scriptTag = document.createElement("script");
        scriptTag.src = "/forest/static/d3.min.js";
        document.body.appendChild(scriptTag);
        console.log('d3.js loaded')
    }
}


function hide_menus(){
    for (var i = document.maxfig; i >= 0 ; i--) {
      [...document.querySelectorAll('.barc_g'+i)].forEach(function(d){
          d.style.visibility = i < document.n ? "visible" : "hidden";
          //console.log(i,d)
      })
      
    }
}

/* Switch to/from "modal" context */
function openModal() {
    let els = {
        controls: document.getElementById('controls-container'),
        modal: document.getElementById('modal-container')
    }
    if (els.controls.classList.contains('display-block')) {
        els.controls.classList.remove('display-block')
        els.controls.classList.add('display-none')
        els.modal.classList.remove('display-none')
        els.modal.classList.add('display-block')
    }
}
function closeModal() {
    let els = {
        controls: document.getElementById('controls-container'),
        modal: document.getElementById('modal-container')
    }
    if (els.modal.classList.contains('display-block')) {
        els.modal.classList.remove('display-block')
        els.modal.classList.add('display-none')
        els.controls.classList.remove('display-none')
        els.controls.classList.add('display-block')
    }
}

// Cross-browser full screen
function openFullscreen(el) {
    if (el.requestFullscreen) {
        el.requestFullscreen()
    } else if (el.mozRequestFullScreen) {
        /* Mozilla */
        el.mozRequestFullScreen()
    } else if (el.webkitRequestFullscreen) {
        /* Chrome, Safari, Opera */
        el.webkitRequestFullscreen()
    } else if (el.msRequestFullscreen) {
        /* IE/Edge */
        el.msRequestFullscreen()
    }
}


/* Close fullscreen */
function closeFullscreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.mozCancelFullScreen) { /* Firefox */
    document.mozCancelFullScreen();
  } else if (document.webkitExitFullscreen) { /* Chrome, Safari and Opera */
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) { /* IE/Edge */
    document.msExitFullscreen();
  }
}

function getFullscreenElement() {
    return document.fullscreenElement || /* Standard syntax */
        document.webkitFullscreenElement || /* Chrome, Safari and Opera syntax */
        document.mozFullScreenElement ||/* Firefox syntax */
        document.msFullscreenElement /* IE/Edge syntax */
}

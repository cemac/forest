import {UIEvent} from "core/ui_events"
import * as p from "core/properties"
import {isArray} from "core/util/types"
import {MultiLine} from "models/glyphs/multi_line"
import {Patches} from "models/glyphs/patches"
import {Bezier} from "models/glyphs/bezier"
//import {Circle} from "models/glyphs/circle"
//import {Text} from "models/glyphs/text"
import {PolyTool} from "models/tools/edit/poly_tool"
import {PolyDrawToolView} from "models/tools/edit/poly_draw_tool"
import {bk_tool_icon_poly_draw} from "styles/icons"
//import {patch_to_column} from "models/sources/column_data_source"

export interface HasPolyGlyph {
  glyph: MultiLine | Patches | Bezier
}

export class FrontDrawToolView extends PolyDrawToolView {
  model: FrontDrawTool

  connect_signals(): void {
    super.connect_signals()
    //const bez = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("bezier") > -1); })
    //const bez_ds = bez[0].data_source
    const text_stamps = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("text_stamp") > -1); })
    const text_ds = text_stamps[0].data_source
    this.connect(this.model.renderers[0].data_source.change, () => text_ds.change.emit())
  }

  _draw(ev: UIEvent, mode: string, emit: boolean = false): void {
    const renderer = this.model.renderers[0]
    const bez = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("bezier") > -1); })
    const bez_ds = bez[0].data_source
    const bez2 = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("bezier2") > -1); })
    const bez2_ds = bez2[0].data_source
    const point = this._map_drag(ev.sx, ev.sy, renderer)

    if (!this._initialized)
      this.activate() // Ensure that activate has been called

    if (point == null)
      return

    const [x, y] = this._snap_to_vertex(ev, ...point)

    const cds = renderer.data_source
    const glyph: any = renderer.glyph
    const bez_glyph: any = bez[0].glyph
    const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
    const [x0key, y0key] = [bez_glyph.x0.field, bez_glyph.y0.field]
    const [cx0key, cy0key] = [bez_glyph.cx0.field, bez_glyph.cy0.field]
    const [cx1key, cy1key] = [bez_glyph.cx1.field, bez_glyph.cy1.field]
    const [x1key, y1key] = [bez_glyph.x1.field, bez_glyph.y1.field]
    if (mode == 'new') {
      this._pop_glyphs(cds, this.model.num_objects)
      if (xkey) cds.get_array(xkey).push([x, x])
      if (ykey) cds.get_array(ykey).push([y, y])
      if (xkey) bez2_ds.get_array(xkey).push([])
      if (ykey) bez2_ds.get_array(ykey).push([])
      if (xkey) bez2_ds.get_array('dx').push([])
      if (ykey) bez2_ds.get_array('dy').push([])
      if (x0key) bez_ds.get_array(x0key).push([null])
      if (y0key) bez_ds.get_array(y0key).push([null])
      if (cx0key) bez_ds.get_array(cx0key).push([null])
      if (cy0key) bez_ds.get_array(cy0key).push([null])
      if (cx1key) bez_ds.get_array(cx1key).push([null])
      if (cy1key) bez_ds.get_array(cy1key).push([null])
      if (x1key) bez_ds.get_array(x1key).push([null])
      if (y1key) bez_ds.get_array(y1key).push([null])
      this._pad_empty_columns(cds, [xkey, ykey])
      //this._pad_empty_columns(bez2_ds, [xkey, ykey])
    } else if (mode == 'edit') {
      if (xkey) {
        const xs = cds.data[xkey][cds.data[xkey].length-1]
        xs[xs.length-1] = x
      }
      if (ykey) {
        const ys = cds.data[ykey][cds.data[ykey].length-1]
        ys[ys.length-1] = y
      }
      if(xkey && ykey) {
        this._drawFront(mode)
      }
    } else if (mode == 'add') {
      if (xkey) {
        const xidx = cds.data[xkey].length-1
        let xs = cds.get_array<number[]>(xkey)[xidx]
        const nx = xs[xs.length-1]
        xs[xs.length-1] = x
        if (!isArray(xs)) {
          xs = Array.from(xs)
          cds.data[xkey][xidx] = xs
        }
        xs.push(nx)
      }
      if (ykey) {
        const yidx = cds.data[ykey].length-1
        let ys = cds.get_array<number[]>(ykey)[yidx]
        const ny = ys[ys.length-1]
        ys[ys.length-1] = y
        if (!isArray(ys)) {
          ys = Array.from(ys)
          cds.data[ykey][yidx] = ys
        }
        ys.push(ny)
      }
      if(xkey && ykey) {
        this._drawFront(mode)
      }
     }
     this._emit_cds_changes(bez_ds, true, false, emit)
     this._emit_cds_changes(bez2_ds, true, false, emit)
     //bez_ds.change.emit()
     this._emit_cds_changes(cds, true, false, emit)
     //cds.change.emit()
  }

  _drawFront(mode: string): void {
    const renderer = this.model.renderers[0]
    const glyph: any = renderer.glyph
    const bez = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("bezier") > -1); })
    const bez2 = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("bezier2") > -1); })
    const cds = renderer.data_source
    const bez_ds = bez[0].data_source
    const bez2_ds = bez2[0].data_source
    const bez_glyph: any = bez[0].glyph
    const [xkey, ykey] = [glyph.xs.field, glyph.ys.field]
    const [x0key, y0key] = [bez_glyph.x0.field, bez_glyph.y0.field]
    const [cx0key, cy0key] = [bez_glyph.cx0.field, bez_glyph.cy0.field]
    const [cx1key, cy1key] = [bez_glyph.cx1.field, bez_glyph.cy1.field]
    const [x1key, y1key] = [bez_glyph.x1.field, bez_glyph.y1.field]
    let offset = 0
    if(mode =="add") {
        offset = 1;
    }
    let xidx = cds.data[xkey].length-1
    const xlen = cds.data[xkey][xidx].length - offset
    //let xlen = 0
    //xlen = cds.data[xkey][xidx].length - offset
    if(xlen > 3)
    {
       if(xlen ==4 || (xlen-1) % 3 == 0 || (!this._drawing && xlen % 3 == 0) ) //last clause should catch closing double-taps
       {
        for(var i=0; i < (xlen/3); i+=1) {
          const beznumber = Math.floor((xlen/3) - 1) //integer. using Floor because xlen=4 for the first one.
          //const beznumber = i //integer. using Floor because xlen=4 for the first one.
          //xs and ys are one longer than in the 'edit' stanza
          const xs = cds.data[xkey][cds.data[xkey].length-1]
          const ys = cds.data[ykey][cds.data[ykey].length-1]

          let bezlength = 0;
          cds.get_array(xkey).forEach(
            function(each: []) { 
                  if(each != cds.data[xkey][xidx])
                  {
                     bezlength += Math.floor((each.length /3)) // i.e. the same as xlen but for all of them except the current one
                  }
               }
          );

          const x0 = bez_ds.get_array<number>(x0key)
          const y0 = bez_ds.get_array<number>(y0key)
          const cx0 = bez_ds.get_array<number>(cx0key)
          const cy0 = bez_ds.get_array<number>(cy0key)
          const cx1 = bez_ds.get_array<number>(cx1key)
          const cy1 = bez_ds.get_array<number>(cy1key)
          const x1 = bez_ds.get_array<number>(x1key)
          const y1 = bez_ds.get_array<number>(y1key)
        
          let beztot = beznumber + bezlength
         
          x0[beztot] = xs[3*beznumber +0]
          y0[beztot] = ys[3*beznumber +0]
          cx0[beztot] = xs[3*beznumber +1]
          cy0[beztot] = ys[3*beznumber +1]
          cx1[beztot] = xs[3*beznumber +2]
          cy1[beztot] = ys[3*beznumber +2]
          x1[beztot] = xs[3*beznumber +3]
          y1[beztot] = ys[3*beznumber +3]

          //draw text to fit curve
          if(mode == "add" || this._drawing == false) { //a new point has been added *or* editing has ended

          //calculate coeffcients (per http://www.planetclegg.com/projects/WarpingTextToSplines.html x0=x0, x1=cx0, x2=cx1, x3=x1 etc.)
          const A = x1[beztot] - 3*cx1[beztot] + 3*cx0[beztot] - x0[beztot]
          const B = 3 * cx1[beztot] - 6 * cx0[beztot] + 3 * x0[beztot]
          const C = 3 * cx0[beztot] - 3 * x0[beztot]
          const D = x0[beztot]

          const E = y1[beztot] - 3 * cy1[beztot] + 3 * cy0[beztot] - y0[beztot]
          const F = 3 * cy1[beztot] - 6 * cy0[beztot] + 3 * y0[beztot]
          const G = 3 * cy0[beztot] - 3 * y0[beztot]
          const H = y0[beztot]

          //calculate arc-length (approximately)
          const segments = 200 //number of segments
          let temp_x = []
          let temp_y = []
          let temp_l = [0]
          let temp2_x: number[]=[] //for parallel polyline approximation
          let temp2_y: number[]=[] 
          let temp2_dx: number[]=[]
          let temp2_dy: number[]=[]
          //Calculating text stamp locations with ' +segments+' segments')
          for(var i=0; i < segments; i+=1)
          {
              let t = i/segments
              temp_x.push(A*t**3 + B*t**2 +C*t +D) //At³ + Bt² + Ct + D
              temp_y.push(E*t**3 + F*t**2 +G*t +H)
              if(i>0){
                 temp_l.push(Math.sqrt((temp_x[temp_x.length-1]-temp_x[temp_x.length-2])**2 + (temp_y[temp_y.length-1]-temp_y[temp_y.length-2])**2)+temp_l[temp_l.length-1])
              }
          }
            
          const total_length = temp_l[temp_l.length-1]
          const spacing = (this.parent.model.y_range.end - this.parent.model.y_range.start)/15

          //drawing text stamps over '+total_length
          //draw points, text glyph at each one
          const ts = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("text_stamp") > -1); })
          //how many figures?
          const figlist = new Set([].concat.apply([],(ts.map(a => a.glyph.tags))).filter(function(tag: string) { return tag.startsWith("fig"); })) //list of figure tags
          let fignum =0;
          figlist.forEach(function(figtag: string) { 
          let order=0
          const ts_fig = ts.filter(function(element) { return (element.glyph.tags.indexOf(figtag) > -1); })
          for(var i=0.0; i < total_length; i+=spacing)
          {
              //i is target arc length
              const i_index = temp_l.findIndex(l => l >= i) || 1 //Index of first element larger or equal to i


              let t = temp_l[i_index] / total_length //default if i is already in the table
              if(temp_l[i_index] > i) //if not
              {
                 //interpolate
                 const segmentFraction = (i - temp_l[i_index-1]) / (temp_l[i_index] - temp_l[i_index-1])
                 t = (temp_l[i_index -1] + segmentFraction) / total_length  // 1.x × 
              }
              if(t > 1) 
              {
                 t= 1;
              }

              //calculate angle of text 
              let dx = 3*A*t**2 + 2*B*t + C //derivatives of previous
              let dy = 3*E*t**2 + 2*F*t + G

            
              let text_ds = ts_fig[order % ts_fig.length].data_source
              order++; //cycle through input characters/strings (there is 1 CDS each)
              const ts_glyph: any = ts_fig[0].glyph
              const [ts_xkey, ts_ykey, ts_fontsizekey, ts_anglekey] = [ts_glyph.x.field, ts_glyph.y.field, ts_glyph.text_font_size.field, ts_glyph.angle.field]
              text_ds.get_array(ts_xkey).push(A*t**3 + B*t**2 +C*t +D) //At³ + Bt² + Ct + D
              text_ds.get_array(ts_ykey).push(E*t**3 + F*t**2 +G*t +H)
              text_ds.get_array(ts_fontsizekey).push(null)
              text_ds.get_array('datasize').push(null)
              text_ds.get_array(ts_anglekey).push(Math.atan2(dy,dx))
              text_ds.change.emit();
          }
              
          for(var i=0.0; i < total_length; i+=(spacing/4)) 
          {
              //calculate polyline vertices (same as text stamps, but more frequent)
              //i is target arc length
              const i_index = temp_l.findIndex(l => l >= i) || 1 //Index of first element larger or equal to i
              let t = temp_l[i_index] / total_length //default if i is already in the table
              if(temp_l[i_index] > i) //if not
              {
                 //interpolate
                 const segmentFraction = (i - temp_l[i_index-1]) / (temp_l[i_index] - temp_l[i_index-1])
                 t = (temp_l[i_index -1] + segmentFraction) / total_length  // 1.x × 
              }
              if(t > 1) 
              {
                 t= 1;
              }

              if(fignum==0)
              {
                  //draw polyline approximating Bezier, same size as textstamps
                  temp2_x.push(A*t**3 + B*t**2 +C*t +D) 
                  temp2_y.push(E*t**3 + F*t**2 +G*t +H)
                  let dx = 3*A*t**2 + 2*B*t + C //derivatives of previous
                  let dy = 3*E*t**2 + 2*F*t + G
                  temp2_dx.push(dx)// [-dy, dx] is the normal vector to the segment
                  temp2_dy.push(dy)
              }
          }
          fignum++;
          })
          bez2_ds.data['xs'][xidx] = bez2_ds.data['xs'][xidx].concat(temp2_x, [x1[beztot]])
          bez2_ds.data['ys'][xidx] = bez2_ds.data['ys'][xidx].concat(temp2_y, [y1[beztot]])
          bez2_ds.data['dx'][xidx] = bez2_ds.data['dx'][xidx].concat(temp2_dx, [3*A + 2*B + C]) //i.e. dy/dx for t=1
          bez2_ds.data['dy'][xidx] = bez2_ds.data['dy'][xidx].concat(temp2_dy, [3*E + 2*F + G])
          bez2_ds.change.emit();
          
         } 
        }
       }
     }
    }
  activate(): void {
    /*const multiline_ds = this.model.renderers.filter(function(element) { return (element.glyph.tags.indexOf("multiline") > -1); })
    for(const ml_ds of multiline_ds) {
        const mds = ml_ds.data_source
        mds.connect(mds.properties.data.change, () => this._drawFront('edit'))
    }*/
    if (!this.model.vertex_renderer || !this.model.active)
      return
    this._show_vertices()
    if (!this._initialized) {
      for (const renderer of this.model.renderers) {
        const cds = renderer.data_source
        cds.connect(cds.properties.data.change, () => this._show_vertices())
      }
    }
    this._initialized = true
  }
}

export namespace FrontDrawTool {
  export type Attrs = p.AttrsOf<Props>

  export type Props = PolyTool.Props & {
    drag: p.Property<boolean>
    num_objects: p.Property<number>
  }
}

export interface FrontDrawTool extends FrontDrawTool.Attrs {}

export class FrontDrawTool extends PolyTool {
  properties: FrontDrawTool.Props
  __view_type__: FrontDrawToolView

  constructor(attrs?: Partial<FrontDrawTool.Attrs>) {
    super(attrs)
  }

  static init_FrontDrawTool(): void {
    this.prototype.default_view = FrontDrawToolView

  }

  tool_name = "Polygon Draw Tool"
  icon = bk_tool_icon_poly_draw
  event_type = ["pan" as "pan", "tap" as "tap", "move" as "move"]
  default_order = 3
}


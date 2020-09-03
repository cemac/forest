import {XYGlyph} from "models/glyphs/xy_glyph"
import {Text, TextView, TextData} from "models/glyphs/text"
import {TextVector} from "core/property_mixins"
import * as visuals from "core/visuals"
import * as p from "core/properties"

export interface TextStampData extends TextData {
}

export interface TextStampView extends TextStampData {}

export class TextStampView extends TextView {
  model: TextStamp
  visuals: TextStamp.Visuals

}

export namespace TextStamp {
  export type Attrs = p.AttrsOf<Props>

  export type Props = Text.Props

  export type Mixins = TextVector

  export type Visuals = XYGlyph.Visuals & {text: visuals.Text}
}

export interface TextStamp extends TextStamp.Attrs {}

export class TextStamp extends Text {
  properties: Text.Props
  __view_type__: TextStampView

  constructor(attrs?: Partial<TextStamp.Attrs>) {
    super(attrs)
  }

  static init_TextStamp(): void {
    this.prototype.default_view = TextStampView

  }
}

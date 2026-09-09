import React from 'react';
import {Easing,interpolate,useCurrentFrame} from 'remotion';
import {EvidenceZoom} from '../fxkit';

export type EvidenceBeats={expand:number;focus:number;conclude:number;return:number};

/** A persistent support image becomes the main view, then returns to the explanation.
 * Mount this inside a content area, never around chrome, narration or subtitles.
 */
export const EvidenceBridge:React.FC<{
  src:string;label:string;beats:EvidenceBeats;frame?:number;fx?:number;fy?:number;
  width:number;height:number;inset:{x:number;y:number;scale:number};children:React.ReactNode;
}>=({src,label,beats,frame,fx=.5,fy=.5,width,height,inset,children})=>{
  const current=useCurrentFrame(),f=frame??current;
  if(!(beats.expand>=0&&beats.focus>=beats.expand+18&&beats.conclude>beats.focus&&beats.return>beats.conclude)
      ||![inset.x,inset.y,inset.scale,width,height].every(Number.isFinite)
      ||width<=0||height<=0||inset.scale<=0||inset.scale>1||inset.x<0||inset.y<0
      ||inset.x+width*inset.scale>width||inset.y+height*inset.scale>height){
    throw new Error('Invalid evidence beats or inset outside content viewport');
  }
  const ramp=(a:number,b:number)=>interpolate(f,[a,b],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp',easing:Easing.inOut(Easing.cubic)});
  const back=ramp(beats.return,beats.return+18);
  const takeover=ramp(beats.expand,beats.expand+18)*(1-back);
  const scale=inset.scale+(1-inset.scale)*takeover;
  // Rewind only the local image focus on return; the film/audio clock never changes.
  const imageFrame=back>0?beats.conclude-(beats.conclude-beats.focus)*back:f;
  return <div style={{position:'relative',width,height,overflow:'hidden'}}>
    <div style={{position:'absolute',inset:0,opacity:1-takeover}}>{children}</div>
    <div style={{position:'absolute',left:0,top:0,transformOrigin:'0 0',transform:`translate(${inset.x*(1-takeover)}px,${inset.y*(1-takeover)}px) scale(${scale})`}}>
      <EvidenceZoom src={src} label={takeover>.99&&back===0?label:undefined} frame={imageFrame} fx={fx} fy={fy} focusAt={beats.focus} concludeAt={beats.conclude} style={{width,height}}/>
    </div>
  </div>;
};

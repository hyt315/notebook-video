export const focusTransform = (width:number,height:number,fx:number,fy:number,zoom:number,progress:number) => {
  if (![width,height,fx,fy,zoom,progress].every(Number.isFinite) || width<=0 || height<=0 || zoom<1 || fx<0 || fx>1 || fy<0 || fy>1) {
    throw new Error('Invalid image focus: positive viewport, zoom >= 1 and normalized focal point required');
  }
  const p=Math.max(0,Math.min(1,progress));
  const scale=1+(zoom-1)*p;
  // Clamp to the scaled viewport, so a focal point near an edge never exposes empty pixels.
  const x=Math.max(width*(1-scale),Math.min(0,(width/2-fx*width*zoom)*p));
  const y=Math.max(height*(1-scale),Math.min(0,(height/2-fy*height*zoom)*p));
  return {scale,x,y,transform:`translate(${x}px,${y}px) scale(${scale})`};
};

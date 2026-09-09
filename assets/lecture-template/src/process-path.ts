type Point={x:number;y:number};
export type BranchRoute={start:Point;knee:Point;control:Point;turn:Point;end:Point};
export const branchPath=(r:BranchRoute)=>`M${r.start.x} ${r.start.y} L${r.knee.x} ${r.knee.y} Q${r.control.x} ${r.control.y} ${r.turn.x} ${r.turn.y} L${r.end.x} ${r.end.y}`;
const mix=(a:Point,b:Point,t:number)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t});
export const followBranch=(r:BranchRoute,progress:number):Point=>{
  const p=Math.max(0,Math.min(1,progress));
  if(p<=.72) return mix(r.start,r.knee,p/.72);
  if(p>=.92) return mix(r.turn,r.end,(p-.92)/.08);
  const t=(p-.72)/.2;
  return mix(mix(r.knee,r.control,t),mix(r.control,r.turn,t),t);
};

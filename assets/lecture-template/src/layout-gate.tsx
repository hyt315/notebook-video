import {useLayoutEffect} from 'react';
import {cancelRender, continueRender, delayRender, useCurrentFrame} from 'remotion';

// Measures static card layout, not transformed collisions or narrative completeness.
export const CardFitGate=()=>{
  const frame=useCurrentFrame();
  useLayoutEffect(()=>{
    const handle=delayRender(`measuring cards at frame ${frame}`);
    let live=true;
    Promise.all([document.fonts.load('400 40px Kai'),document.fonts.load('700 40px Kai'),document.fonts.load('600 40px Clash'),document.fonts.load('500 40px Space'),document.fonts.ready]).then(()=>{
      if(!live) return;
      const bad:string[]=[];
      const opaque=(el:HTMLElement)=>{
        const s=getComputedStyle(el);
        const alpha=s.backgroundColor.match(/rgba?\([^)]*\)/)?.[0];
        return !!alpha && alpha!=='rgba(0, 0, 0, 0)' && parseFloat(s.borderTopWidth)>0;
      };
      document.querySelectorAll<HTMLElement>('div,span').forEach(el=>{
        if(!el.textContent?.trim()||el.children.length||el.closest('[data-fit-skip]')) return;
        let card:HTMLElement|null=el.parentElement;
        while(card&&card!==document.body&&!card.hasAttribute('data-fit-card')&&!opaque(card)) card=card.parentElement;
        if(!card||card===document.body||parseInt(getComputedStyle(card).zIndex||'0',10)>=140||!card.clientWidth) return;
        let x=0,y=0,node:HTMLElement|null=el;
        while(node&&node!==card){x+=node.offsetLeft;y+=node.offsetTop;node=node.offsetParent as HTMLElement|null;}
        if(node!==card) return;
        if(x< -2||y< -2||x+el.offsetWidth>card.clientWidth+2||y+el.offsetHeight>card.clientHeight+2||el.scrollWidth>el.clientWidth+2){
          bad.push(el.textContent.trim().slice(0,24));
        }
      });
      if(bad.length) cancelRender(new Error(`Card overflow at frame ${frame}: ${bad.slice(0,4).join(' | ')}`));
      else continueRender(handle);
    }).catch(error=>{if(live) cancelRender(error);});
    return ()=>{live=false;continueRender(handle);};
  },[frame]);
  return null;
};

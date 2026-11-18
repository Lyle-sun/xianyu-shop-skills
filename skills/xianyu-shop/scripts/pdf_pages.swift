import PDFKit; import AppKit
let a=CommandLine.arguments; let doc=PDFDocument(url:URL(fileURLWithPath:a[1]))!
print("pages",doc.pageCount)
for s in a[3...] { let i=Int(s)!-1; guard let p=doc.page(at:i) else{continue}
 let r=p.bounds(for:.mediaBox); let sc:CGFloat=1600/r.width
 let img=NSImage(size:NSSize(width:r.width*sc,height:r.height*sc)); img.lockFocus()
 NSColor.white.set(); NSRect(x:0,y:0,width:r.width*sc,height:r.height*sc).fill()
 let c=NSGraphicsContext.current!.cgContext; c.scaleBy(x:sc,y:sc); p.draw(with:.mediaBox,to:c); img.unlockFocus()
 let rep=NSBitmapImageRep(data:img.tiffRepresentation!)!; try! rep.representation(using:.jpeg,properties:[.compressionFactor:0.85])!.write(to:URL(fileURLWithPath:"\(a[2])/p\(s).jpg")) }

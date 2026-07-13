// Convert a portrait photo into ASCII art for the hero banner.
//
//   swift tools/photo_to_ascii.swift <image> <cols> <cellAspect> > tools/portrait.txt
//
// cellAspect is charWidth/lineHeight of the target monospace cell, so the ASCII
// keeps the photo's proportions instead of looking stretched.
//
// The background (bright green bokeh) is masked out by hue + brightness, which
// keeps the dark green hoodie as part of the subject. Isolated dark leaf-gaps are
// then dropped by keeping only the largest connected region and filling holes.

import Cocoa

let args = CommandLine.arguments
let path = args[1]
let COLS = Int(args[2]) ?? 66
let CELL_ASPECT = Double(args[3]) ?? 0.52   // charWidth / lineHeight

// sparse -> dense; index 0 is empty (background)
let RAMP = Array(" .:^~!7?JY5PGB#&@")

guard let src = NSImage(contentsOfFile: path),
      let cg = src.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    FileHandle.standardError.write("cannot load \(path)\n".data(using: .utf8)!)
    exit(1)
}

/// Render a sub-rect of the image down to cols x rows and return per-cell RGB.
func sample(_ image: CGImage, crop: CGRect, cols: Int, rows: Int) -> [[(Double, Double, Double)]] {
    let cropped = image.cropping(to: crop) ?? image
    var buf = [UInt8](repeating: 0, count: cols * rows * 4)
    let cs = CGColorSpaceCreateDeviceRGB()
    let ctx = CGContext(data: &buf, width: cols, height: rows, bitsPerComponent: 8,
                        bytesPerRow: cols * 4, space: cs,
                        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.interpolationQuality = .high
    ctx.draw(cropped, in: CGRect(x: 0, y: 0, width: cols, height: rows))

    var out = [[(Double, Double, Double)]]()
    for y in 0..<rows {
        var row = [(Double, Double, Double)]()
        for x in 0..<cols {
            let i = (y * cols + x) * 4
            row.append((Double(buf[i]), Double(buf[i + 1]), Double(buf[i + 2])))
        }
        out.append(row)
    }
    return out
}

func luma(_ p: (Double, Double, Double)) -> Double {
    0.2126 * p.0 + 0.7152 * p.1 + 0.0722 * p.2
}

/// Subject mask: skin, hair, ear and neck are all red-dominant (g-r between -8 and
/// -43 in this photo), while the foliage bokeh is green-dominant (+6 to +35) at every
/// brightness. The hoodie is green-dominant too (+22), so it drops out with the
/// background — the portrait is head-and-neck.
func subjectMask(_ px: [[(Double, Double, Double)]]) -> [[Bool]] {
    let rows = px.count, cols = px[0].count
    var m = [[Bool]](repeating: [Bool](repeating: false, count: cols), count: rows)
    for y in 0..<rows {
        for x in 0..<cols {
            let p = px[y][x]
            m[y][x] = p.0 > p.1 + 2      // r > g
        }
    }
    return m
}

/// Keep only the largest 4-connected true-region.
func largestComponent(_ m: [[Bool]]) -> [[Bool]] {
    let rows = m.count, cols = m[0].count
    var label = [[Int]](repeating: [Int](repeating: 0, count: cols), count: rows)
    var sizes = [0]
    var cur = 0
    for y in 0..<rows {
        for x in 0..<cols where m[y][x] && label[y][x] == 0 {
            cur += 1
            var n = 0
            var stack = [(y, x)]
            label[y][x] = cur
            while let (cy, cx) = stack.popLast() {
                n += 1
                for (dy, dx) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
                    let ny = cy + dy, nx = cx + dx
                    if ny >= 0, ny < rows, nx >= 0, nx < cols, m[ny][nx], label[ny][nx] == 0 {
                        label[ny][nx] = cur
                        stack.append((ny, nx))
                    }
                }
            }
            sizes.append(n)
        }
    }
    guard sizes.count > 1 else { return m }
    let best = (1..<sizes.count).max(by: { sizes[$0] < sizes[$1] })!
    var out = [[Bool]](repeating: [Bool](repeating: false, count: cols), count: rows)
    for y in 0..<rows { for x in 0..<cols { out[y][x] = label[y][x] == best } }
    return out
}

/// Fill background pockets that don't touch the border (eye sockets, glasses gaps).
func fillHoles(_ m: [[Bool]]) -> [[Bool]] {
    let rows = m.count, cols = m[0].count
    var outside = [[Bool]](repeating: [Bool](repeating: false, count: cols), count: rows)
    var stack = [(Int, Int)]()
    for y in 0..<rows {
        for x in [0, cols - 1] where !m[y][x] && !outside[y][x] {
            outside[y][x] = true; stack.append((y, x))
        }
    }
    for x in 0..<cols {
        for y in [0, rows - 1] where !m[y][x] && !outside[y][x] {
            outside[y][x] = true; stack.append((y, x))
        }
    }
    while let (cy, cx) = stack.popLast() {
        for (dy, dx) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
            let ny = cy + dy, nx = cx + dx
            if ny >= 0, ny < rows, nx >= 0, nx < cols, !m[ny][nx], !outside[ny][nx] {
                outside[ny][nx] = true
                stack.append((ny, nx))
            }
        }
    }
    var out = m
    for y in 0..<rows { for x in 0..<cols where !m[y][x] && !outside[y][x] { out[y][x] = true } }
    return out
}

let W = cg.width, H = cg.height

// Pass 1: coarse mask to find the subject's bounding box in image space.
let probeCols = 120
let probeRows = Int(Double(probeCols) * Double(H) / Double(W))
let probe = sample(cg, crop: CGRect(x: 0, y: 0, width: W, height: H), cols: probeCols, rows: probeRows)
let pm = fillHoles(largestComponent(subjectMask(probe)))

var minX = probeCols, maxX = 0, minY = probeRows, maxY = 0
for y in 0..<probeRows {
    for x in 0..<probeCols where pm[y][x] {
        minX = min(minX, x); maxX = max(maxX, x)
        minY = min(minY, y); maxY = max(maxY, y)
    }
}
let sx = Double(W) / Double(probeCols), sy = Double(H) / Double(probeRows)
let pad = 1.0
let cropRect = CGRect(x: (Double(minX) - pad) * sx,
                      y: (Double(minY) - pad) * sy,   // CGImage.cropping origin is top-left
                      width: (Double(maxX - minX) + 2 * pad) * sx,
                      height: (Double(maxY - minY) + 2 * pad) * sy)
    .intersection(CGRect(x: 0, y: 0, width: W, height: H))

// Pass 2: sample the cropped subject at the final grid.
let ROWS = max(1, Int((Double(COLS) * cropRect.height / cropRect.width * CELL_ASPECT).rounded()))
let px = sample(cg, crop: cropRect, cols: COLS, rows: ROWS)
let mask = fillHoles(largestComponent(subjectMask(px)))

// Contrast-normalize luminance across subject pixels only.
var vals = [Double]()
for y in 0..<ROWS { for x in 0..<COLS where mask[y][x] { vals.append(luma(px[y][x])) } }
vals.sort()
let lo = vals[Int(Double(vals.count) * 0.02)]
let hi = vals[Int(Double(vals.count) * 0.98)]

var lines = [String]()
for y in 0..<ROWS {
    var s = ""
    for x in 0..<COLS {
        if !mask[y][x] { s.append(" "); continue }
        var t = (luma(px[y][x]) - lo) / max(1, hi - lo)
        t = min(max(t, 0), 1)
        t = pow(t, 1.15)   // deepen shadows: the lit face should carry the portrait
        // No floor — the darkest hair falls to empty space, so the face reads as a face
        // instead of the head filling in as one solid textured blob.
        let idx = min(RAMP.count - 1, Int(t * Double(RAMP.count - 1) + 0.5))
        s.append(RAMP[idx])
    }
    lines.append(s)
}

// Trim fully-empty edge rows, keep columns aligned.
while let f = lines.first, f.trimmingCharacters(in: .whitespaces).isEmpty { lines.removeFirst() }
while let l = lines.last, l.trimmingCharacters(in: .whitespaces).isEmpty { lines.removeLast() }

print(lines.map { $0.replacingOccurrences(of: "\\s+$", with: "", options: .regularExpression) }
    .joined(separator: "\n"))
FileHandle.standardError.write("grid \(COLS)x\(ROWS), crop \(cropRect)\n".data(using: .utf8)!)

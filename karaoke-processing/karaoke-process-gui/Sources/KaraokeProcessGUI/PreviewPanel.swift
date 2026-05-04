import SwiftUI

struct PreviewPanel: View {
    let image: NSImage?
    let label: String
    let isLoading: Bool
    var showAspectBorder: Bool = false

    var body: some View {
        VStack(spacing: 4) {
            ZStack {
                Color.black
                if let image {
                    if showAspectBorder {
                        Image(nsImage: image)
                            .resizable()
                            .aspectRatio(aspectRatio(of: image), contentMode: .fit)
                            .overlay(Rectangle().stroke(Color.white, lineWidth: 2))
                            .padding(6)
                    } else {
                        Image(nsImage: image)
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                    }
                }
                if isLoading {
                    ProgressView().controlSize(.small).tint(.white)
                } else if image == nil {
                    Text("No preview yet")
                        .foregroundColor(.secondary)
                        .font(.callout)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.bottom, 4)
        }
    }

    private func aspectRatio(of image: NSImage) -> CGFloat {
        let w = image.size.width
        let h = image.size.height
        guard w > 0, h > 0 else { return 16.0 / 9.0 }
        return w / h
    }
}

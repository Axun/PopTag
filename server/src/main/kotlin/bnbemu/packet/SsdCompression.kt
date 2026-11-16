package bnbemu.packet

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.Deflater

/** Preserve the SSD data; use the format's zlib envelope for large tables. */
internal fun compressLargeSsd(block: ByteArray): ByteArray {
    require(block.size >= 6 && block[0] == 0x18.toByte() && block[5] == 0.toByte())
    if (block.size < 60_000) return block
    val compressor = Deflater(9)
    val compressed = ByteArrayOutputStream()
    try {
        compressor.setInput(block, 6, block.size - 6)
        compressor.finish()
        val buffer = ByteArray(8192)
        while (!compressor.finished()) {
            val count = compressor.deflate(buffer)
            check(count > 0) { "SSD compressor made no progress" }
            compressed.write(buffer, 0, count)
        }
    } finally { compressor.end() }
    val data = compressed.toByteArray()
    if (data.size + 10 >= block.size) return block
    return ByteBuffer.allocate(data.size + 10).order(ByteOrder.LITTLE_ENDIAN)
        .put(0x18.toByte()).putInt(data.size + 5).put(1.toByte())
        .putInt(block.size - 6).put(data).array()
}

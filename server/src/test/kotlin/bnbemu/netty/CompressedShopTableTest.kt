package bnbemu.netty

import bnbemu.packet.*
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.util.zip.Inflater
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test

class CompressedShopTableTest {
    private fun verify(original: ByteArray) {
        val encoded = compressLargeSsd(original)
        val header = ByteBuffer.wrap(encoded).order(ByteOrder.LITTLE_ENDIAN)
        assertEquals(0x18.toByte(), header.get())
        assertEquals(encoded.size - 5, header.int)
        assertEquals(1.toByte(), header.get())
        val length = header.int
        assertEquals(original.size - 6, length)
        val result = ByteArray(length)
        val inflater = Inflater()
        try {
            inflater.setInput(encoded,10,encoded.size-10)
            var read = 0
            while (!inflater.finished() && read < result.size) {
                val n = inflater.inflate(result,read,result.size-read)
                assertTrue(n > 0)
                read += n
            }
            assertEquals(result.size,read)
            assertTrue(inflater.finished())
            assertEquals(0,inflater.remaining)
        } finally { inflater.end() }
        assertArrayEquals(original.copyOfRange(6,original.size),result)
        assertTrue(encoded.size < 60_000, "Actual table must fit a small frame for this diagnostic")
    }
    @Test fun expandedDefinitionsPreserveEveryByte() = verify(ItemDef.buildBlock(ItemDef.DEFAULT_ITEMS))
    @Test fun expandedCatalogPreservesEveryByteAndUsesWireChecksum() {
        val block=ShopCatalog.buildBlock(ShopCatalog.DEFAULT_ITEMS)
        verify(block)
        val compressed=compressLargeSsd(block)
        assertEquals(ShopCatalog.adler32Zero(compressed,5,compressed.size-5),ShopCatalog.CATALOG_HASH)
    }
    @Test fun smallLegacyBlockRemainsIdentical() {
        val block=ItemDef.buildBlock(ItemDef.DEFAULT_ITEMS.take(3))
        assertSame(block,compressLargeSsd(block))
    }
}

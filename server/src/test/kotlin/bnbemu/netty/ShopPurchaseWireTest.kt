package bnbemu.netty

import bnbemu.packet.*
import bnbemu.server.*
import io.netty.buffer.Unpooled
import io.netty.channel.embedded.EmbeddedChannel
import org.junit.jupiter.api.Assertions.*
import org.junit.jupiter.api.Test
import java.util.UUID

class ShopPurchaseWireTest {
    private fun buy(channel: EmbeddedChannel, product: Int): List<PKT> {
        val request=Unpooled.buffer()
        SendPacketBase(request,3).apply { Encode2(267);Encode4(product);Encode4(0);Encode1(0) }
        channel.writeInbound(request)
        return buildList { while (true) add(channel.readOutbound<PKT>() ?: break) }
    }

    @Test fun actualPurchaseDispatchDoesNotInsertTheNativeCreatedStockTwice() {
        OpcodeManager.recvOps
        // Test real listed bubble/face/decoration/nameplate products, rather
        // than just the standalone account-to-inventory helper.
        for(category in listOf(14,19,10,18)) {
            val p=ShopCatalog.DEFAULT_ITEMS.first { it.category==category && it.tail.price1 in 1..1_000_000 }
            val socket=ClientSocket();val channel=EmbeddedChannel(socket)
            try {
                val user=User(socket,91007,"purchase-wire-${UUID.randomUUID()}")
                socket.users.add(user)
                val initial=user.lucci
                for (quantity in 1..2) {
                    val replies=buy(channel,p.prodId)
                    assertEquals(listOf(202,122),replies.map { OpcodeManager.getSendOp(it::class.java) },
                        "Native S202 applies stock; a following S274 would insert it again")
                    val body=Unpooled.buffer()
                    try {
                        replies.first().encode(SendPacketBase(body,3))
                        assertEquals(0,body.Decode1)
                    } finally { body.release() }
                    val account=LocalShop.store.account(user.accountKey)
                    assertEquals(quantity*p.count,account.items[p.itemId])
                    assertEquals(initial-quantity*p.tail.price1,account.lucci)
                    assertEquals(account.lucci,user.lucci)
                    assertEquals(1,localInventoryEntries(account,0,emptyList()).count { it.itemId==p.itemId })
                }
            } finally {channel.finishAndReleaseAll()}
        }
    }

    @Test fun rejectedPurchaseDoesNotIssueAnyStockOrMoneyUpdate() {
        OpcodeManager.recvOps
        val socket=ClientSocket();val channel=EmbeddedChannel(socket)
        try {
            val user=User(socket,91008,"rejected-purchase-${UUID.randomUUID()}")
            socket.users.add(user)
            val before=LocalShop.store.account(user.accountKey)
            val replies=buy(channel,Int.MAX_VALUE)
            assertEquals(listOf(202),replies.map { OpcodeManager.getSendOp(it::class.java) })
            val body=Unpooled.buffer()
            try {replies.single().encode(SendPacketBase(body,3));assertEquals(1,body.Decode1)} finally {body.release()}
            assertEquals(before,LocalShop.store.account(user.accountKey))
        } finally {channel.finishAndReleaseAll()}
    }
}

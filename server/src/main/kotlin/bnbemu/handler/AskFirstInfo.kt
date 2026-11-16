package bnbemu.handler

import bnbemu.netty.Decode4
import bnbemu.netty.PKTHandler
import bnbemu.packet.AskFirstInfoResult
import bnbemu.netty.Decode1
import bnbemu.netty.Decode2
import bnbemu.netty.PassportServer
import io.netty.buffer.ByteBuf
import bnbemu.ACP

/** EN C2 uses E1(count), repeated E4(byte length)+block-encoded passport IDs. */
internal fun ByteBuf.decodeLocalLoginAccounts(): List<PassportServer.PassportAccount>? {
    val start=readerIndex()
    return try {
        val count=Decode1
        if(count !in 1..2) return null
        val accounts=List(count) {
            val length=Decode4
            if(length !in 1..128 || readableBytes()<length) return null
            val raw=java.io.ByteArrayOutputStream()
            repeat(length/4) {val value=Decode4;repeat(4) {n -> raw.write(value ushr (8*n))}}
            if(length%4>=2) {val value=Decode2;raw.write(value);raw.write(value ushr 8)}
            if(length%2==1) raw.write(Decode1)
            val target=raw.toByteArray().toString(ACP).removePrefix("NGP")
            PassportServer.ACCOUNTS[target.lowercase()] ?: return null
        }
        if(accounts.map {it.userId}.distinct().size!=accounts.size) return null
        accounts
    } catch (_: IndexOutOfBoundsException) { null }
    finally {readerIndex(start)}
}

// server = CLoginPool::OnAskFirstInfo
// EN: 回應 op 4 AskFirstInfoResult (65B), 真實伺服器不回 FirstInfoInit
// (1861B 的 FirstInfoInit 是首連上的主動推送, 見 AskFirstSession.kt)
val AskFirstInfo = PKTHandler { c ->
    val accounts=decodeLocalLoginAccounts()
    println("[LocalLogin] count=${accounts?.size ?: 0}")
    c send AskFirstInfoResult(accounts.orEmpty())
}

package bnbemu.packet

import bnbemu.netty.PKT

/**
 * S->C op 122: 用户动态数据同步 (Lucci / 金币同步)
 *
 * 逆向分析 (CA.exe EN v18):
 * - 派发逻辑: 在 CA.exe `CStage::OnPacket` (0x00502AE1 -> 0x00502EC0) 命中 case 122,
 *   调用 0x004F80D0 解析本包.
 * - 包体结构:
 *   1. Encode1(propertyId) —— 本地玩家序号：0=1P，1=2P。
 *      6E6109逐人读取用户缓存时也把循环序号传给6E4E23；
 *      旧注释误将第二名玩家的余额解释为段位积分。
 *   2. Encode4(value)      —— 属性数值 (如 5000)
 * - 客户端处理:
 *   0x004F80D0 读取后调用 `CUserDynamicInfo::Instance().Set(propertyId, value)` (0x006E4E23),
 *   存入对应玩家的安全变量 (CProtectedInt)，经0x005062E9校验金币上限。
 *
 * 历史背景:
 * 抓包中 [Encode1(0)][Encode4(5000)] 曾被误推为 "疑似 5 秒定时器", 实为初始金币 Lucci=5000,
 * 与 AskFirstInfoResult (op 4) 的 v31=5000 及 Nexon Passport 0x2E 初始金币完全对应.
 */
fun UserDynamicInfo(propertyId: Int = 0, value: Int = 5000) = PKT {
    Encode1(propertyId)
    Encode4(value)
}

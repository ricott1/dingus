LSK = 10**8
PUB_KEY_LENGTH = 32
ADDRESS_LENGTH = 20

EVENT_TAGS = [
    "user_input",
    "service_subscription",
    "api_response"
]

NETWORKS = {
    "testnet": bytes.fromhex("15f0dacc1060e91818224a94286b13aa04279c640bd5d6f193182031d133df7c"),
    "mainnet": bytes.fromhex("4c09e6a781fc4c7bdb936ee815de8f94190f8a7519becd9de2081832be309a99"),
    "piratenet": bytes.fromhex("1c66ba124e8c350600d820bca357760617f56b4dee7d3b8d8f7a4b2ae9475b53"),
    "devnet": bytes.fromhex("10e9885844847412420c1aa28195cf754be187173a9e94b47459e543ab6b8092")
}
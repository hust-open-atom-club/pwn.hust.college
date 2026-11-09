import pytest

#pylint:disable=redefined-outer-name,use-dict-literal,missing-timeout,unspecified-encoding,consider-using-with,unused-argument

from utils import container_exec

MONITORING_ACCEPT_RULES = [
    ["-i", "user_network", "-p", "tcp", "--dport", "3000", "-j", "ACCEPT"],
    ["-i", "user_network", "-p", "tcp", "--dport", "9090", "-j", "ACCEPT"],
    ["-o", "user_network", "-p", "tcp", "--sport", "3000", "-j", "ACCEPT"],
    ["-o", "user_network", "-p", "tcp", "--sport", "9090", "-j", "ACCEPT"],
]

UNRELATED_RULE = ["-i", "user_network", "-d", "203.0.113.7", "-j", "ACCEPT"]


def docker_user_rules():
    result = container_exec("iptables", "-S", "DOCKER-USER")
    return result.stdout.splitlines()


def rule_matches(rules, rule):
    return any(all(part in line for part in rule) for line in rules)


def test_legacy_monitoring_rules_are_purged_and_rerun_is_stable():
    # older dojo-init versions inserted the monitoring allow rules on every
    # run, so deployments can carry several duplicates of each
    for rule in MONITORING_ACCEPT_RULES:
        for _ in range(3):
            container_exec("iptables", "-I", "DOCKER-USER", *rule)
    container_exec("iptables", "-I", "DOCKER-USER", *UNRELATED_RULE)

    rules = docker_user_rules()
    assert rule_matches(rules, MONITORING_ACCEPT_RULES[0]), "预期已插入重复放行规则"
    assert rule_matches(rules, UNRELATED_RULE)

    container_exec("/opt/pwn.college/dojo/dojo-init")

    rules = docker_user_rules()
    for rule in MONITORING_ACCEPT_RULES:
        assert not rule_matches(rules, rule), f"dojo-init 后仍残留监控放行规则: {rule}"
    assert rule_matches(rules, UNRELATED_RULE), "无关规则不应被清理"

    # rerunning must neither reintroduce the monitoring rules nor duplicate
    # anything else
    container_exec("/opt/pwn.college/dojo/dojo-init")
    rules_after_rerun = docker_user_rules()
    assert rules_after_rerun == rules, "dojo-init 重复执行应保持 DOCKER-USER 规则不变"

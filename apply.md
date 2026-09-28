---
layout: page
title: 申请私密账号
permalink: /apply/
---

<div class="container" style="max-width: 520px">
  <h2 class="mb-1">申请私密空间账号</h2>
  <p class="text-muted mb-4">填写信息提交申请，<strong>站长审核通过后</strong>账号方可使用。</p>

  <form id="applyForm" onsubmit="return false">
    <div class="mb-3">
      <label class="form-label">账号（3-20 位字母 / 数字 / 下划线）</label>
      <input id="f-user" class="form-control" autocomplete="off" />
    </div>
    <div class="mb-3">
      <label class="form-label">密码（至少 8 位）</label>
      <input type="password" id="f-pass" class="form-control" autocomplete="new-password" />
    </div>
    <div class="mb-3">
      <label class="form-label">确认密码</label>
      <input type="password" id="f-pass2" class="form-control" autocomplete="new-password" />
    </div>
    <div class="mb-3">
      <label class="form-label">姓名</label>
      <input id="f-name" class="form-control" autocomplete="off" />
    </div>
    <div class="mb-3">
      <label class="form-label">电话</label>
      <input id="f-phone" class="form-control" autocomplete="off" placeholder="11 位手机号" />
    </div>
    <button id="f-submit" class="btn btn-primary">生成申请</button>
  </form>

  <div id="f-msg" class="text-danger mt-3"></div>

  <div id="f-result" class="d-none mt-4">
    <div class="alert alert-success">✅ 申请已加密生成，别人无法查看。请复制下方密文发给站长审核：</div>
    <textarea id="f-cipher" class="form-control" rows="4" readonly></textarea>
    <button id="f-copy" class="btn btn-outline-primary mt-2">复制密文</button>
    <p class="text-muted small mt-3">站长微信：联系朱柘名本人获取最新联系方式。审核通过后，用你的账号和密码访问
      <a href="/private/">私密空间</a>。</p>
  </div>
</div>

<script>
  (function () {
    var PUBLIC_KEY_PEM = '-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAq7oBcYJIHaiK7QT1N1r0\nU6p3WEfZ+vp60SRDuMtcVghiVKuFkOGoWuhPjC2yRWP8GQ5U3Lu84ByTaWSSv+D4\n5ET42Ulm8pf3BnuhUh2pFnvg4ig/UIV+Veh24DmFyMesDBMc0MefBME2+wJ+m+j0\nX7Uh7dNes1zPD6nHNQkF96jmoF4PqZVo5BBkqXl/OPVoeS7NEvPg2xMg6PUBy+tE\n5QCZI0fl2/o5w5F84c1nDpJtgJdcVehsYg+6n3mQ1qiEl49NMlnASv+ezjbY8w3y\nl8CDFZ7nCN/LQQi3zrnSo1t8BcB9Fy5PiJqqplb/SRCRGnD5WKswZZOgO1T2lFec\naQIDAQAB\n-----END PUBLIC KEY-----';

    var userEl = document.getElementById("f-user");
    var passEl = document.getElementById("f-pass");
    var pass2El = document.getElementById("f-pass2");
    var nameEl = document.getElementById("f-name");
    var phoneEl = document.getElementById("f-phone");
    var submitBtn = document.getElementById("f-submit");
    var msgEl = document.getElementById("f-msg");
    var resultEl = document.getElementById("f-result");
    var cipherEl = document.getElementById("f-cipher");
    var copyBtn = document.getElementById("f-copy");

    function b64FromBytes(bytes) {
      var bin = "";
      for (var i = 0; i < bytes.length; i += 8192) {
        bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
      }
      return btoa(bin);
    }

    async function encryptApply(data) {
      var body = PUBLIC_KEY_PEM.replace(/-----(BEGIN|END) PUBLIC KEY-----|\n/g, "");
      var der = Uint8Array.from(atob(body), function (c) { return c.charCodeAt(0); });
      var key = await crypto.subtle.importKey(
        "spki", der, { name: "RSA-OAEP", hash: "SHA-256" }, false, ["encrypt"]
      );
      var ct = await crypto.subtle.encrypt(
        { name: "RSA-OAEP" },
        key,
        new TextEncoder().encode(data)
      );
      return b64FromBytes(new Uint8Array(ct));
    }

    submitBtn.addEventListener("click", async function () {
      msgEl.textContent = "";
      var user = userEl.value.trim();
      var pass = passEl.value;
      var pass2 = pass2El.value;
      var name = nameEl.value.trim();
      var phone = phoneEl.value.trim();

      if (!/^[a-zA-Z0-9_]{3,20}$/.test(user)) {
        msgEl.textContent = "账号需为 3-20 位字母/数字/下划线";
        return;
      }
      if (pass.length < 8) {
        msgEl.textContent = "密码至少 8 位";
        return;
      }
      if (pass !== pass2) {
        msgEl.textContent = "两次输入的密码不一致";
        return;
      }
      if (!name) {
        msgEl.textContent = "请填写姓名";
        return;
      }
      if (!/^1\d{10}$/.test(phone)) {
        msgEl.textContent = "请填写 11 位手机号";
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "加密中…";
      try {
        var data = JSON.stringify({
          user: user, pass: pass, name: name, phone: phone,
          ts: new Date().toISOString()
        });
        var cipher = await encryptApply(data);
        cipherEl.value = cipher;
        resultEl.classList.remove("d-none");
        msgEl.textContent = "";
        // 清空敏感输入，防止浏览器或剪贴板残留
        passEl.value = "";
        pass2El.value = "";
      } catch (e) {
        msgEl.textContent = "加密失败，请重试或联系站长";
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "生成申请";
      }
    });

    copyBtn.addEventListener("click", function () {
      cipherEl.select();
      try {
        document.execCommand("copy");
        copyBtn.textContent = "已复制 ✓";
        setTimeout(function () { copyBtn.textContent = "复制密文"; }, 2000);
      } catch (e) {}
    });
  })();
</script>

import java.time.Instant;
import java.util.Map;

/** Java 21, no external dependencies. Local policy example, not a provider SDK. */
public class IdentityPolicyDemo {
    enum Fact { PHONE_CONTROL, EMAIL_CONTROL, IDENTITY_CHECKED, ACCOUNT_AUTHENTICATED }
    enum Action { VERIFY_PHONE, IDENTITY_REQUIRED_ONBOARDING, SIGN_IN }

    // Created by the server after checking a trusted provider's response.
    // subjectId is an account or a server-bound pre-signup session, not a phone number.
    record Evidence(String subjectId, Fact fact, String policyId, Instant expiresAt) {}
    record Requirement(Fact fact, String policyId) {}

    static final Map<Action, Requirement> REQUIREMENTS = Map.of(
        Action.VERIFY_PHONE, new Requirement(Fact.PHONE_CONTROL, "phone-v1"),
        Action.IDENTITY_REQUIRED_ONBOARDING,
            new Requirement(Fact.IDENTITY_CHECKED, "identity-v1"),
        Action.SIGN_IN, new Requirement(Fact.ACCOUNT_AUTHENTICATED, "login-v1")
    );

    // BEFORE: a phone check can accidentally authorize identity-required onboarding.
    static boolean allowBefore(boolean verified) {
        return verified;
    }

    // AFTER: action and sub (expected subject) come from the server's request context.
    static boolean allow(Action action,
            String sub, Evidence e,
            Instant now) {
        Requirement r =
            REQUIREMENTS.get(action);
        return r != null
            && e != null
            && sub.equals(e.subjectId())
            && now.isBefore(e.expiresAt())
            && e.fact() == r.fact()
            && r.policyId()
                .equals(e.policyId());
    }

    static void check(String label, boolean actual, boolean expected) {
        if (actual != expected) throw new AssertionError(label);
        System.out.println(label + ": " + (actual ? "ALLOW" : "DENY"));
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-09-30T00:00:00Z");
        Instant expiry = now.plusSeconds(300);
        Evidence sms = new Evidence("user-a", Fact.PHONE_CONTROL, "phone-v1", expiry);
        Evidence sna = new Evidence("user-a", Fact.PHONE_CONTROL, "phone-v1", expiry);
        Evidence email = new Evidence("user-a", Fact.EMAIL_CONTROL, "email-v1", expiry);
        Evidence identity = new Evidence("user-a", Fact.IDENTITY_CHECKED, "identity-v1", expiry);
        Evidence passkey = new Evidence("user-a", Fact.ACCOUNT_AUTHENTICATED, "login-v1", expiry);

        check("Before: SMS -> identity onboarding", allowBefore(true), true);
        check("SMS -> phone", allow(Action.VERIFY_PHONE, "user-a", sms, now), true);
        check("SMS -> identity onboarding",
            allow(Action.IDENTITY_REQUIRED_ONBOARDING, "user-a", sms, now), false);
        check("SNA -> identity onboarding",
            allow(Action.IDENTITY_REQUIRED_ONBOARDING, "user-a", sna, now), false);
        check("Email -> phone", allow(Action.VERIFY_PHONE, "user-a", email, now), false);
        check("Identity -> identity onboarding",
            allow(Action.IDENTITY_REQUIRED_ONBOARDING, "user-a", identity, now), true);
        check("Passkey -> sign-in", allow(Action.SIGN_IN, "user-a", passkey, now), true);
        check("Passkey -> identity onboarding",
            allow(Action.IDENTITY_REQUIRED_ONBOARDING, "user-a", passkey, now), false);
        check("Wrong subject", allow(Action.SIGN_IN, "user-b", passkey, now), false);
        check("Expired", allow(Action.SIGN_IN, "user-a", passkey, expiry), false);
        Evidence otherPolicy = new Evidence("user-a", Fact.IDENTITY_CHECKED, "other-v1", expiry);
        check("Wrong policy",
            allow(Action.IDENTITY_REQUIRED_ONBOARDING, "user-a", otherPolicy, now), false);
        check("Missing evidence", allow(Action.SIGN_IN, "user-a", null, now), false);
        System.out.println("12 checks passed");
    }
}

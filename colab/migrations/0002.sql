/* actions are now site actions */
ALTER TABLE object_feeds_subscription_actions RENAME TO object_feeds_subscription_site_actions;

/* add the same table but for emails */
CREATE TABLE "object_feeds_subscription_email_actions" (
    "id" serial NOT NULL PRIMARY KEY,
    "subscription_id" integer NOT NULL,
    "action_id" integer NOT NULL,
    UNIQUE ("subscription_id", "action_id")
);
ALTER TABLE "object_feeds_subscription_email_actions" ADD CONSTRAINT "subscription_id_refs_id_e53ac6a4" FOREIGN KEY ("subscription_id") REFERENCES "object_feeds_subscription" ("id") DEFERRABLE INITIALLY DEFERRED;


buildscript {
    repositories { google(); mavenCentral() }
    dependencies {
        classpath("com.android.tools.build:gradle:9.5.2")
        // AGP uses built-in Kotlin; update its plugin without applying a second one.
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.21")
        // Security floors for AGP transitives. Keep these off the app classpath.
        classpath(platform("org.bouncycastle:bc-jdk18on-bom:1.87"))
        constraints {
            classpath("com.google.guava:guava:33.8.0-jre")
            classpath("org.apache.commons:commons-lang3:3.22.0")
            classpath("org.bitbucket.b_c:jose4j:0.9.7")
            classpath("org.jdom:jdom2:2.0.6.1")
        }
    }
}

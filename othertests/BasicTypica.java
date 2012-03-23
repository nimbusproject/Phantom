import java.util.ArrayList;
import java.util.List;
import java.security.SecureRandom;
import java.math.BigInteger;

import com.xerox.amazonws.ec2.AutoScaling;
import com.xerox.amazonws.ec2.LaunchConfiguration;
import com.xerox.amazonws.ec2.AutoScalingGroup;

public class BasicTypica {

    public static void main(String[] args) throws Exception {
        AutoScaling autoScaling = new AutoScaling("", "", false, "svc.uc.futuregrid.org", 8445);     
        //AutoScaling autoScaling = new AutoScaling("", "", false);
        SecureRandom random = new SecureRandom();
        String name = new BigInteger(130, random).toString(32);

        LaunchConfiguration lc;
        lc = new LaunchConfiguration(name, "debian-tutorial.gz", 1, 1);
        //lc = new LaunchConfiguration(name, "ami-51db1138", 1, 5);
        System.out.println("Creating " + name);
        autoScaling.createLaunchConfiguration(lc);
        System.out.println("Deleting " + name);
        autoScaling.deleteLaunchConfiguration(name);

        System.out.println("re-creating " + name);
        autoScaling.createLaunchConfiguration(lc);
        List<String> configs = new ArrayList<String>();
        configs.add(name);
        System.out.println("listing " + name);
        List<LaunchConfiguration> groups = autoScaling.describeLaunchConfigurations(configs);
        for(LaunchConfiguration group : groups) {
            System.out.println(group.toString());
        }

        List<String> azlist = new ArrayList<String>();
        azlist.add("hotel");
        //azlist.add("us-east-1b");
        String asgname = new BigInteger(130, random).toString(32);
        System.out.println("create autoscae group " + asgname);
        autoScaling.createAutoScalingGroup(asgname,
            name, 1, 5, 1, azlist);

        System.out.println("set capacity " + asgname);
        autoScaling.setDesiredCapacity(asgname, 2);
        List<String> asgs = new ArrayList<String>();
        asgs.add(asgname);
        System.out.println("list " + asgname);
        List<AutoScalingGroup> xl = autoScaling.describeAutoScalingGroups(asgs);
        for(AutoScalingGroup group : xl) {
            System.out.println(group.toString());
        }
        System.out.println("delete " + asgname);
        autoScaling.deleteAutoScalingGroup(asgname);
    }
}
